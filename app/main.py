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
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                video_title = info_dict.get("title", "audio")
                video_ext = info_dict.get("ext", None)
                video_file = os.path.join(temp_dir, f"{video_title}.{video_ext}")

            if not os.path.exists(video_file):
                raise Exception("Erro ao baixar o vídeo.")

            mp3_file = os.path.join(temp_dir, f"{video_title}.mp3")
            audio = AudioSegment.from_file(video_file)

            if len(audio) == 0:
                raise Exception("Erro ao extrair áudio do vídeo.")

            audio.export(mp3_file, format="mp3")

            global current_progress
            current_progress = 90

            output_file = os.path.join(DOWNLOAD_FOLDER, f"{video_title}.mp3")
            shutil.copy2(mp3_file, output_file)

            current_progress = 100

            for connection in active_connections:
                try:
                    await connection.send_text(json.dumps({
                        "type": "complete",
                        "percent": 100,
                        "message": "Conversão concluída!"
                    }))
                except:
                    pass

            return {"file_name": f"{video_title}.mp3"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao converter o vídeo: {str(e)}"
        )

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

@app.get("/progress")
async def get_progress():
    return {"percent": current_progress}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            if data:  # Verifica se há dados
                print(f"Recebido do WebSocket: {data}")
    except WebSocketDisconnect:
        print("Cliente desconectado do WebSocket")
        active_connections.remove(websocket)
    except Exception as e:
        print(f"Erro no WebSocket: {str(e)}")
        active_connections.remove(websocket)

@app.get("/download/{file_name}")
async def download_mp3(file_name: str):
    file_path = os.path.join(DOWNLOAD_FOLDER, file_name)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/mpeg", filename=file_name)
    else:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
