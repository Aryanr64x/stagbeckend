import numpy as np
from scipy.io.wavfile import read as read_wav, write as write_wav
import os

def pad_audio_to_match(aud1, aud2):
    """Pads aud2 to match the shape of aud1"""
    if len(aud1.shape) != len(aud2.shape):
        raise ValueError("Audio shapes mismatch")
    padded = np.zeros_like(aud1)
    limit = min(len(aud2), len(padded))
    padded[:limit] = aud2[:limit]
    return padded

def embed_audio(cover_path, secret_path, stego_path):
    rate_cover, cover = read_wav(cover_path)
    rate_secret, secret = read_wav(secret_path)

    if rate_cover != rate_secret:
        raise ValueError("Sampling rates do not match")

    # Convert to mono if stereo
    if cover.ndim > 1:
        cover = cover[:, 0]
    if secret.ndim > 1:
        secret = secret[:, 0]

    # Normalize both to float32
    cover = cover.astype(np.float32)
    secret = secret.astype(np.float32)

    # Pad secret to match cover length
    if len(secret) < len(cover):
        print("Padding secret audio to match cover detail length...")
        secret = np.pad(secret, (0, len(cover) - len(secret)))
    else:
        print("Trimming secret to match cover length...")
        secret = secret[:len(cover)]

    # Perform FFT on both
    cover_fft = np.fft.fft(cover)
    secret_fft = np.fft.fft(secret)

    # Embed secret magnitude into cover phase
    stego_fft = cover_fft + 0.01 * secret_fft  # secret hidden in low amplitude

    # IFFT back to time domain
    stego_time = np.fft.ifft(stego_fft).real

    # Normalize and convert back to int16
    stego_time = np.int16(stego_time / np.max(np.abs(stego_time)) * 32767)

    # Save stego audio
    write_wav(stego_path, rate_cover, stego_time)
    print(f"✅ Embedded and saved: {stego_path}")

def recover_audio(stego_path, recovered_path):
    rate_stego, stego = read_wav(stego_path)

    if stego.ndim > 1:
        stego = stego[:, 0]

    stego = stego.astype(np.float32)

    # FFT of stego
    stego_fft = np.fft.fft(stego)

    # Roughly reverse the embedding (scale assumed same as in embed)
    recovered_fft = (stego_fft - np.fft.fft(np.zeros_like(stego))) / 0.01
    recovered_time = np.fft.ifft(recovered_fft).real

    # Normalize and convert to int16
    recovered_time = np.int16(recovered_time / np.max(np.abs(recovered_time)) * 32767)

    write_wav(recovered_path, rate_stego, recovered_time)
    print(f"✅ Recovered and saved: {recovered_path}")
