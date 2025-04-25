from fastapi import APIRouter
from ..schemas import TextToTextEmbedRequest, TextToTextRecoverRequest
router = APIRouter()

# ----- Core Logic -----
def text_to_binary(text: str) -> str:
    return ''.join(format(ord(c), '08b') for c in text)

def binary_to_zwc(binary: str) -> str:
    return ''.join('\u200B' if bit == '0' else '\u200C' for bit in binary)

def embed_secret(cover_text: str, secret: str):
    binary = text_to_binary(secret)
    zwc_encoded = binary_to_zwc(binary)
    position = len(cover_text) // 2
    embedded_text = cover_text[:position] + zwc_encoded + cover_text[position:]

    logs = {
        "original_secret": secret,
        "binary_representation": binary,
        "zwc_encoded": zwc_encoded.replace('\u200B', '␣0').replace('\u200C', '␣1'),
        "insertion_position": position,
        "cover_text_length": len(cover_text),
        "embedded_text_length": len(embedded_text)
    }
    
    return embedded_text, logs

def zwc_to_binary(zwc_text: str) -> str:
    return ''.join('0' if c == '\u200B' else '1' for c in zwc_text)

def binary_to_text(binary: str) -> str:
    chars = [binary[i:i+8] for i in range(0, len(binary), 8)]
    return ''.join(chr(int(c, 2)) for c in chars)

# ----- Routes -----
@router.post("/embed/text-to-text-zwc")
def embed(req: TextToTextEmbedRequest):
    embedded, logs = embed_secret(req.cover, req.secret)
    zwc_part = ''.join(c for c in embedded if c in ['\u200B', '\u200C'])
    return {
        "embedded_text": embedded,
        "zwc_count": len(zwc_part),
        "binary_len": len(logs["binary_representation"]),
        "logs": logs
    }

@router.post("/recover/text-to-text-zwc")
def recover(req: TextToTextRecoverRequest):
    zwc_only = ''.join(c for c in req.embedded if c in ['\u200B', '\u200C'])

    if not zwc_only:
        return {"error": "No zero-width characters found in embedded text."}

    binary = zwc_to_binary(zwc_only)
    recovered = binary_to_text(binary)

    logs = {
        "zwc_found_length": len(zwc_only),
        "zwc_visual": zwc_only.replace('\u200B', '␣0').replace('\u200C', '␣1'),
        "recovered_binary": binary,
        "recovered_text": recovered
    }

    return {
        "recovered_secret": recovered,
        "logs": logs
    }


