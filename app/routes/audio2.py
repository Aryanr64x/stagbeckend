from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse
from .utils import embed_audio, recover_audio
import os

router = APIRouter()
TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

@router.post("/embed")
async def embed_audio_route(
    cover: UploadFile = File(...),
    secret: UploadFile = File(...)
):
    cover_path = os.path.join(TEMP_DIR, "cover.wav")
    secret_path = os.path.join(TEMP_DIR, "secret.wav")
    stego_path = os.path.join(TEMP_DIR, "stego.wav")

    # Save uploaded files
    with open(cover_path, "wb") as f:
        f.write(await cover.read())
    with open(secret_path, "wb") as f:
        f.write(await secret.read())

    try:
        embed_audio(cover_path, secret_path, stego_path)
    except Exception as e:
        return {"error": str(e)}

    return FileResponse(stego_path, media_type="audio/wav", filename="stego.wav")

@router.post("/recover")
async def recover_audio_route(
    stego: UploadFile = File(...)
):
    stego_path = os.path.join(TEMP_DIR, "stego.wav")
    recovered_path = os.path.join(TEMP_DIR, "recovered.wav")

    # Save uploaded stego file
    with open(stego_path, "wb") as f:
        f.write(await stego.read())

    try:
        recover_audio(stego_path, recovered_path)
    except Exception as e:
        return {"error": str(e)}

    return FileResponse(recovered_path, media_type="audio/wav", filename="recovered.wav")
