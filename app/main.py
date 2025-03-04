from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import yt_dlp
from pydub import AudioSegment
import os
import tempfile

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

            output_file = os.path.join(DOWNLOAD_FOLDER, f"{video_title}.mp3")
            os.rename(mp3_file, output_file)

            return {"file_name": f"{video_title}.mp3"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Falha ao converter o vídeo: {str(e)}"
        )


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
