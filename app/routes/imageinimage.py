from fastapi import APIRouter, File, UploadFile, Form
from fastapi.responses import StreamingResponse, JSONResponse
from PIL import Image
import io

router = APIRouter()


def hide_image(cover: Image.Image, secret: Image.Image) -> Image.Image:
    secret = secret.resize(cover.size).convert("RGB")
    cover = cover.convert("RGB")

    cover_pixels = cover.load()
    secret_pixels = secret.load()

    for y in range(cover.height):
        for x in range(cover.width):
            r1, g1, b1 = cover_pixels[x, y]
            r2, g2, b2 = secret_pixels[x, y]

            # Embed top 4 bits from secret into LSBs of cover
            r = (r1 & 0b11110000) | (r2 >> 4)
            g = (g1 & 0b11110000) | (g2 >> 4)
            b = (b1 & 0b11110000) | (b2 >> 4)

            cover_pixels[x, y] = (r, g, b)

    return cover


def reveal_image(stego: Image.Image) -> Image.Image:
    stego = stego.convert("RGB")
    stego_pixels = stego.load()

    secret = Image.new("RGB", stego.size)
    secret_pixels = secret.load()

    for y in range(stego.height):
        for x in range(stego.width):
            r, g, b = stego_pixels[x, y]

            # Extract LSBs and shift back to MSB position
            r_secret = (r & 0b00001111) << 4
            g_secret = (g & 0b00001111) << 4
            b_secret = (b & 0b00001111) << 4

            secret_pixels[x, y] = (r_secret, g_secret, b_secret)

    return secret


@router.post("/embed/image-in-image")
async def embed_image_in_image(
    cover: UploadFile = File(...),
    secret: UploadFile = File(...)
):
    try:
        cover_img = Image.open(io.BytesIO(await cover.read()))
        secret_img = Image.open(io.BytesIO(await secret.read()))

        stego_img = hide_image(cover_img, secret_img)

        output_stream = io.BytesIO()
        stego_img.save(output_stream, format="PNG")
        output_stream.seek(0)

        return StreamingResponse(output_stream, media_type="image/png", headers={
            "Content-Disposition": "attachment; filename=stego_image.png"
        })

    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


@router.post("/recover/image-in-image")
async def recover_image_from_stego(
    embedded: UploadFile = File(...)
):
    try:
        stego_img = Image.open(io.BytesIO(await embedded.read()))
        recovered_img = reveal_image(stego_img)

        output_stream = io.BytesIO()
        recovered_img.save(output_stream, format="PNG")
        output_stream.seek(0)

        return StreamingResponse(output_stream, media_type="image/png", headers={
            "Content-Disposition": "attachment; filename=recovered_secret_image.png"
        })

    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
