from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse, JSONResponse
from PIL import Image
import io

router = APIRouter()

def embed_text_multichannel(cover_img: Image.Image, secret: str):
    length_prefix = format(len(secret), '016b')
    secret_binary = ''.join(format(ord(char), '08b') for char in secret)
    binary = length_prefix + secret_binary

    pixels = cover_img.load()
    width, height = cover_img.size

    max_capacity = width * height * 3
    if len(binary) > max_capacity:
        raise ValueError("Secret is too long to embed in this image.")

    idx = 0
    for y in range(height):
        for x in range(width):
            if idx >= len(binary):
                break
            r, g, b = pixels[x, y]
            if idx < len(binary): r = (r & ~1) | int(binary[idx]); idx += 1
            if idx < len(binary): g = (g & ~1) | int(binary[idx]); idx += 1
            if idx < len(binary): b = (b & ~1) | int(binary[idx]); idx += 1
            pixels[x, y] = (r, g, b)
        if idx >= len(binary):
            break

    logs = {
        "secret_length": len(secret),
        "binary_length": len(binary),
        "image_dimensions": f"{width}x{height}",
        "pixels_used": (idx + 2) // 3,
        "capacity_available": max_capacity,
        "percent_used": f"{(idx / max_capacity) * 100:.2f}%"
    }

    return cover_img, logs


def extract_text_multichannel(img: Image.Image):
    pixels = img.load()
    width, height = img.size

    bits = ""
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            bits += str(r & 1)
            bits += str(g & 1)
            bits += str(b & 1)

    msg_length = int(bits[:16], 2)
    total_bits = 16 + (msg_length * 8)
    message_bits = bits[16:total_bits]

    chars = [message_bits[i:i+8] for i in range(0, len(message_bits), 8)]
    text = ''.join(chr(int(c, 2)) for c in chars)

    logs = {
        "image_dimensions": f"{width}x{height}",
        "total_bits_read": len(bits),
        "message_length_from_prefix": msg_length,
        "total_bits_for_message": total_bits,
        "pixels_scanned": (total_bits + 2) // 3,
        "binary_preview": message_bits[:64] + ("..." if len(message_bits) > 64 else "")
    }

    return text, logs


@router.post("/embed/text-in-image-lsb-rgb")
async def embed_text_multi(
    secret: str = Form(...),
    cover: UploadFile = File(...)
):
    image_bytes = await cover.read()
    pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    try:
        embedded_image, logs = embed_text_multichannel(pil_image, secret)
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

    output_stream = io.BytesIO()
    embedded_image.save(output_stream, format="PNG")
    output_stream.seek(0)

    headers = {
        "Content-Disposition": "attachment; filename=embedded_image.png",
        "X-Logs-Secret-Length": str(logs["secret_length"]),
        "X-Logs-Binary-Length": str(logs["binary_length"]),
        "X-Logs-Image-Size": logs["image_dimensions"],
        "X-Logs-Pixels-Used": str(logs["pixels_used"]),
        "X-Logs-Percent-Used": logs["percent_used"],
    }

    return StreamingResponse(output_stream, media_type="image/png", headers=headers)


@router.post("/recover/text-in-image-lsb-rgb")
async def recover_text_multi(
    embedded: UploadFile = File(...)
):
    image_bytes = await embedded.read()
    pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    try:
        secret_text, logs = extract_text_multichannel(pil_image)
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

    return {
        "recovered_secret": secret_text,
        "logs": logs
    }
