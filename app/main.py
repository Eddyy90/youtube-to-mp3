from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import yt_dlp
from pydub import AudioSegment
import os
import tempfile
import shutil
import json
import asyncio
import zipfile
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/downloads", StaticFiles(directory=DOWNLOAD_FOLDER), name="downloads")

active_connections = set()
current_progress = 0

@app.get("/")
async def index():
    return FileResponse("static/index.html")


def create_zip():
    timestamp = int(time.time())
    zip_filename = f"playlist_download_{timestamp}.zip"
    zip_path = os.path.join(DOWNLOAD_FOLDER, zip_filename)
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file_name in os.listdir(DOWNLOAD_FOLDER):
            if file_name.lower().endswith(".mp3"):
                file_path = os.path.join(DOWNLOAD_FOLDER, file_name)
                zipf.write(file_path, arcname=file_name)
    return zip_path


def clean_download_folder():
    for file_name in os.listdir(DOWNLOAD_FOLDER):
        file_path = os.path.join(DOWNLOAD_FOLDER, file_name)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Erro ao apagar {file_path}: {e}")


@app.post("/convert/")
async def convert_to_mp3(url: str = Query(...)):
    
    if not url:
        raise HTTPException(status_code=400, detail="URL do vídeo não fornecida.")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": os.path.join(temp_dir, "%(title)s.%(ext)s"),
                "progress_hooks": [progress_hook],
                "quiet": False,
                "ignoreerrors": True,
                "noplaylist": False,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            entries = info.get('entries', [info])

            output_files = []

            for entry in entries:
                if entry is None:
                    continue
                video_title = entry.get('title', 'audio').replace("/", "-").replace("\\", "-")
                video_ext = entry.get('ext', 'webm')
                video_file = os.path.join(temp_dir, f"{video_title}.{video_ext}")

                if not os.path.exists(video_file):
                    continue

                mp3_file = os.path.join(temp_dir, f"{video_title}.mp3")
                audio = AudioSegment.from_file(video_file)
                if len(audio) == 0:
                    continue
                audio.export(mp3_file, format="mp3")

                output_path = os.path.join(DOWNLOAD_FOLDER, f"{video_title}.mp3")
                shutil.copy2(mp3_file, output_path)

                output_files.append(f"{video_title}.mp3")

            global current_progress
            current_progress = 100

            for connection in active_connections:
                try:
                    await connection.send_text(json.dumps({
                        "type": "complete",
                        "percent": 100,
                        "message": "Conversão concluída!",
                        "files": output_files
                    }))
                except Exception as e:
                    print(f"Erro ao enviar atualização de progresso: {str(e)}")
                    active_connections.remove(connection)

            zip_path = create_zip()
            return {"files": output_files, "zip_file": zip_path}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao converter: {str(e)}"
        )


# Progress bar
def progress_hook(d):
    if d["status"] == "downloading":
        global current_progress
        current_progress = float(d.get("_percent_str", "0.0%").replace("%", ""))

        for connection in active_connections:
            try:
                asyncio.create_task(connection.send_text(json.dumps({
                    "type": "progress",
                    "percent": current_progress,
                    "speed": d.get("speed", "0.0"),
                    "eta": d.get("eta", 0)
                })))
            except Exception as e:
                print(f"Erro ao enviar atualização de progresso: {str(e)}")
                active_connections.remove(connection)


# Progress bar
@app.get("/progress")
async def get_progress():
    return {"percent": current_progress}


# WebSocket
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            if data:
                print(f"Recebido do WebSocket: {data}")
    except WebSocketDisconnect:
        print("Cliente desconectado do WebSocket")
        active_connections.remove(websocket)
    except Exception as e:
        print(f"Erro no WebSocket: {str(e)}")
        active_connections.remove(websocket)


# Download
@app.get("/download/{file_name}")
async def download_mp3(file_name: str):
    file_path = os.path.join(DOWNLOAD_FOLDER, file_name)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/mpeg", filename=file_name)
    else:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")


# Listar arquivos
@app.get("/list-downloads")
async def list_downloads():
    files = []
    for file_name in os.listdir(DOWNLOAD_FOLDER):
        if file_name.lower().endswith(".mp3"):
            files.append(file_name)
    return {"files": files}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
