from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
import io
from .pc import PhaseCoding  # Import your PhaseCoding class

# Initialize PhaseCoding instance
phase_coding = PhaseCoding()

router = APIRouter()

# Endpoint to encode audio with secret text and return as streaming response
@router.post("/embed/text-in-audio-pc")
async def encode_audio(
    secret: str = Form(...),  # Use Form to accept secret text
    audio: UploadFile = File(...),  # Accept audio file
):
    # Save the uploaded file
    try:
        audio_content = await audio.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading the file: {str(e)}")
    
    if not secret or len(secret) == 0:
        raise HTTPException(status_code=400, detail="Secret text is required.")

    # Encoding the audio with the secret text
    try:
        # The encode function should take raw audio content and secret text
        encoded_audio = phase_coding.encode(audio_content, secret)

        # Streaming response with the encoded audio (return as a file stream)
        encoded_audio_stream = io.BytesIO(encoded_audio)
        return StreamingResponse(encoded_audio_stream, media_type="audio/wav", headers={"Content-Disposition": "attachment; filename=encoded_audio.wav"})
    
    except Exception as e:
        return HTTPException(status_code=500, detail=f"Error encoding audio: {str(e)}")


# Endpoint to decode the audio and extract the secret message
@router.post("/reveal/text-in-audio-pc")
async def decode_audio(audio: UploadFile = File(...)):
    try:
        # Read the uploaded audio file content
        audio_content = await audio.read()

        # Call the decode method from your PhaseCoding class to extract the secret message
        secret_message = phase_coding.decode_from_bytes(audio_content)
        return {"secret_message": secret_message}
    
    except Exception as e:
        return HTTPException(status_code=500, detail=f"Error decoding audio: {str(e)}")
