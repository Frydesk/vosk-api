import asyncio
import json
import queue
import threading
import wave
from typing import Optional

import sounddevice as sd
import torch
import torchaudio
from fastapi import FastAPI, WebSocket
from vosk import Model, KaldiRecognizer
from silero_vad import SileroVAD

app = FastAPI()

# Global variables
audio_queue = queue.Queue()
is_recording = False
current_transcription = []
model = None
recognizer = None
vad_model = None
vad_utils = None
samplerate = 16000

def load_vad_model():
    """Load Silero VAD model"""
    torch.set_num_threads(1)
    vad = SileroVAD()
    model, utils = vad.load_model()
    return model, utils

def load_vosk_model():
    """Load Vosk model for Spanish"""
    return Model(lang="es")

def callback(indata, frames, time, status):
    """Callback for audio input"""
    if status:
        print(status)
    audio_queue.put(bytes(indata))

def process_audio():
    """Process audio from queue and detect speech"""
    global is_recording, current_transcription
    
    # Initialize VAD parameters
    speech_pad_ms = 100
    min_speech_duration_ms = 250
    min_silence_duration_ms = 100
    
    while is_recording:
        try:
            data = audio_queue.get(timeout=1)
            
            # Convert to tensor for VAD
            audio_tensor = torch.frombuffer(data, dtype=torch.float32)
            
            # Get speech probability using the official package
            speech_prob = vad_model(audio_tensor, samplerate).item()
            
            if speech_prob > 0.5:  # Speech detected
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    if result.get("text"):
                        current_transcription.append(result["text"])
            else:
                # No speech detected, check if we should stop
                if len(current_transcription) > 0:
                    is_recording = False
                    
        except queue.Empty:
            continue
        except Exception as e:
            print(f"Error processing audio: {e}")
            is_recording = False

@app.on_event("startup")
async def startup_event():
    """Initialize models on startup"""
    global model, recognizer, vad_model, vad_utils
    model = load_vosk_model()
    recognizer = KaldiRecognizer(model, samplerate)
    vad_model, vad_utils = load_vad_model()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time transcription"""
    await websocket.accept()
    
    try:
        while True:
            # Wait for start signal
            data = await websocket.receive_text()
            if data == "start":
                global is_recording, current_transcription
                is_recording = True
                current_transcription = []
                
                # Start audio stream
                stream = sd.RawInputStream(
                    samplerate=samplerate,
                    blocksize=8000,
                    dtype="int16",
                    channels=1,
                    callback=callback
                )
                
                with stream:
                    # Start processing thread
                    process_thread = threading.Thread(target=process_audio)
                    process_thread.start()
                    
                    # Wait for processing to complete
                    while is_recording:
                        await asyncio.sleep(0.1)
                    
                    # Send final transcription
                    await websocket.send_text(json.dumps({
                        "status": "complete",
                        "transcription": " ".join(current_transcription)
                    }))
                    
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"} 