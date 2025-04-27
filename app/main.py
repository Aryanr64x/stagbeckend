from fastapi import FastAPI
from .routes import zwcRouter, lsb, imageinimage, deep, textaudio, audio2, unicode, lsbrgb, phase_coding
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)

@app.get("/")
def intro():
    return {"message": "Welcome to ZWC Steganography API 👋"}


app.include_router(zwcRouter.router)
app.include_router(unicode.router)

app.include_router(lsb.router)
app.include_router(imageinimage.router)

app.include_router(deep.router)
app.include_router(textaudio.router)

app.include_router(audio2.router)
app.include_router(lsbrgb.router)


# app.include_router(phase_coding.router)


