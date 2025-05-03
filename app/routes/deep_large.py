from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
import numpy as np
from io import BytesIO
from PIL import Image
from tensorflow.keras.models import load_model
import os

router = APIRouter()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load 128x128 models
steg_model_128 = load_model(os.path.join(BASE_DIR,"models" , "encoder_128_full_1000_more_points.h5"))  
rev_model_128 = load_model(os.path.join(BASE_DIR, "models","decoder_128_full_1000_more_points.h5"), compile=False)   

# Helper to convert uploaded file to 128x128 numpy image
def load_image_128(file: UploadFile) -> np.ndarray:
    img = Image.open(file.file).convert("RGB").resize((128, 128))
    return np.array(img).astype('float32') / 255.0

# Helper to convert numpy image to streaming response (same as before)
def image_response(np_img: np.ndarray):
    img = (np.clip(np_img * 255, 0, 255)).astype('uint8')
    pil_img = Image.fromarray(img)
    buf = BytesIO()
    pil_img.save(buf, format='PNG')
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")

@router.post("/encode/image-to-image-deep")
async def encode_128(secret: UploadFile = File(...), cover: UploadFile = File(...)):
    secret_img = load_image_128(secret)
    cover_img = load_image_128(cover)

    secret_img = np.expand_dims(secret_img, axis=0)
    cover_img = np.expand_dims(cover_img, axis=0)

    stego_img = steg_model_128.predict([secret_img, cover_img])[0]

    return image_response(stego_img)

@router.post("/reveal/image-to-image-deep")
async def decode_128(embedded: UploadFile = File(...)):
    stego_img = load_image_128(embedded)
    stego_img = np.expand_dims(stego_img, axis=0)

    recovered_img = rev_model_128.predict(stego_img)[0]

    return image_response(recovered_img)
