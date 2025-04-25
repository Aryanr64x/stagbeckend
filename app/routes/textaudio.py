from fastapi import APIRouter, UploadFile, File
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
import wave
import struct
import os
import shutil
import uuid

router = APIRouter()

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# Steganography Logic
def encode_wav(input_path, output_path, secret_message):
    audio = wave.open(input_path, mode="rb")
    frame_bytes = bytearray(list(audio.readframes(audio.getnframes())))
    secret_bits = ''.join([bin(ord(i)).lstrip('0b').rjust(8, '0') for i in secret_message])
    message_length = len(secret_bits)
    length_bytes = struct.pack('>I', message_length)
    length_bits = ''.join([bin(byte).lstrip('0b').rjust(8, '0') for byte in length_bytes])
    full_bits = length_bits + secret_bits

    if len(full_bits) > len(frame_bytes):
        raise ValueError("Secret message too large for audio file")

    for i, bit in enumerate(full_bits):
        frame_bytes[i] = (frame_bytes[i] & 254) | int(bit)

    with wave.open(output_path, 'wb') as new_audio:
        new_audio.setparams(audio.getparams())
        new_audio.writeframes(bytes(frame_bytes))
    
    audio.close()


def decode_wav(input_path):
    audio = wave.open(input_path, mode='rb')
    frame_bytes = bytearray(list(audio.readframes(audio.getnframes())))
    length_bits = ''.join([str(frame_bytes[i] & 1) for i in range(32)])
    message_length = struct.unpack('>I', int(length_bits, 2).to_bytes(4, 'big'))[0]
    message_bits = ''.join([str(frame_bytes[i + 32] & 1) for i in range(message_length)])
    decoded = ''.join(chr(int(message_bits[i:i+8], 2)) for i in range(0, len(message_bits), 8))
    audio.close()
    return decoded

# ROUTES
@router.post("/embed/text-in-audio")
async def encode_route(audio: UploadFile = File(...), secret: str = Form(...)):
    try:
        input_path = os.path.join(TEMP_DIR, f"input_{uuid.uuid4()}.wav")
        output_path = os.path.join(TEMP_DIR, f"encoded_{uuid.uuid4()}.wav")

        with open(input_path, "wb") as f:
            shutil.copyfileobj(audio.file, f)

        encode_wav(input_path, output_path, secret)

        return FileResponse(output_path, media_type="audio/wav", filename="encoded_audio.wav")
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/recover/text-in-audio")
async def decode_route(audio: UploadFile = File(...)):
    try:
        input_path = os.path.join(TEMP_DIR, f"decode_{uuid.uuid4()}.wav")
        with open(input_path, "wb") as f:
            shutil.copyfileobj(audio.file, f)

        message = decode_wav(input_path)
        return {"decoded_message": message}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
