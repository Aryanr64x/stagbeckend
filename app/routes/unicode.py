from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..schemas import TextToTextRecoverRequest, TextToTextEmbedRequest
router = APIRouter()

HOMOGLEYPHS = {
    'A': 'А',  # Latin A -> Cyrillic А (U+0410)
    'a': 'а',
    'B': 'Β',  # Latin B -> Greek Beta (U+0392)
    'C': 'Ϲ',
    'E': 'Е',
    'e': 'е',
    'H': 'Н',
    'I': 'І',
    'i': 'і',
    'J': 'Ј',
    'K': 'Κ',
    'M': 'М',
    'O': 'О',
    'o': 'о',
    'P': 'Р',
    'S': 'Ѕ',
    'T': 'Т',
    'X': 'Х',
    'Y': 'Υ',
    'y': 'у',
    'Z': 'Ζ'
}
REV_HOMOGLEYPHS = {v: k for k, v in HOMOGLEYPHS.items()}



# --- Embed Algorithm ---
@router.post("/embed/text-to-text-uh")
def embed_homoglyph(req: TextToTextEmbedRequest):
    cover = req.cover
    secret = req.secret
    binary = ''.join(format(ord(c), '08b') for c in secret)

    # Filter cover indices where homoglyphs are possible
    possible_indices = [i for i, c in enumerate(cover) if c in HOMOGLEYPHS]

    if len(binary) > len(possible_indices):
        raise HTTPException(
        status_code=400,
        detail={
            "message": "Secret too long or cover too short to embed.",
            "binary_length": len(binary),
            "available_slots": len(possible_indices)
         })

    stego_chars = list(cover)
    logs = []

    for bit, idx in zip(binary, possible_indices):
        original_char = stego_chars[idx]
        if bit == '1':
            
            stego_chars[idx] = HOMOGLEYPHS[original_char]
            
            logs.append(f"Bit 1 → Replaced '{original_char}' with '{HOMOGLEYPHS[original_char]}' at position {idx}")
       
        else:
            
            logs.append(f"Bit 0 → Kept '{original_char}' unchanged at position {idx}")

    stego_text = ''.join(stego_chars)

    return {
        "stego_text": stego_text,
        "binary": binary,
        "used_slots": len(binary),
        "logs": logs
    }

# --- Reveal Algorithm ---
@router.post("/recover/text-to-text-uh")
def reveal_homoglyph(req: TextToTextRecoverRequest):
    embedded = req.embedded
    bits = []
    logs = []

    for i, c in enumerate(embedded):
        if c in HOMOGLEYPHS:
            bits.append('0')
            logs.append(f"'{c}' at {i} is a regular char → bit 0")
        elif c in REV_HOMOGLEYPHS:
            bits.append('1')
            logs.append(f"'{c}' at {i} is a homoglyph → bit 1")

    binary = ''.join(bits)
    chars = [chr(int(binary[i:i+8], 2)) for i in range(0, len(binary), 8)]
    recovered = ''.join(chars)

    return {
        "recovered_secret": recovered,
        "binary": binary,
        "logs": logs
    }
