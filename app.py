import asyncio
import json
import queue
import threading
import wave
import logging
from typing import Optional

import sounddevice as sd
import torch
import torchaudio
from fastapi import FastAPI, WebSocket
from vosk import Model, KaldiRecognizer
import silero_vad

# Configure logging to only show errors and critical messages
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Global variables
audio_queue = queue.Queue()
is_recording = False
current_transcription = []
model = None
recognizer = None
vad_model = None
samplerate = 16000

def load_vad_model():
    """Load Silero VAD model"""
    try:
        torch.set_num_threads(1)
        model = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                             model='silero_vad',
                             force_reload=True)
        return model
    except Exception as e:
        logger.error(f"Failed to load Silero VAD model: {str(e)}")
        raise

def load_vosk_model():
    """Load Vosk model"""
    try:
        model = Model(lang="es")
        return model
    except Exception as e:
        logger.error(f"Failed to load Vosk model: {str(e)}")
        raise

def callback(indata, frames, time, status):
    """Callback for audio input"""
    if status:
        logger.error(f"Audio input error: {status}")
    try:
        audio_queue.put(bytes(indata))
    except Exception as e:
        logger.error(f"Error in audio callback: {str(e)}")

def process_audio():
    """Process audio from queue and detect speech"""
    global is_recording, current_transcription
    
    # Initialize VAD parameters
    speech_pad_ms = 100
    min_speech_duration_ms = 250
    min_silence_duration_ms = 100
    silence_frames = 0
    max_silence_frames = 50  # About 2.5 seconds of silence
    speech_detected = False
    wait_frames = 0
    max_wait_frames = 300  # 15 seconds (300 frames at 20ms per frame)
    
    while is_recording:
        try:
            data = audio_queue.get(timeout=1)
            
            # Convert to tensor for VAD
            audio_tensor = torch.frombuffer(data, dtype=torch.float32)
            
            # Get speech probability using the official package
            speech_prob = vad_model(audio_tensor, samplerate).item()
            
            if speech_prob > 0.3:  # Speech detected
                if not speech_detected:
                    speech_detected = True
                silence_frames = 0
                wait_frames = 0  # Reset wait counter when speech is detected
                
                # Process speech with Vosk
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    if result.get("text"):
                        current_transcription.append(result["text"])
            else:
                if speech_detected:
                    silence_frames += 1
                    if silence_frames > max_silence_frames:
                        is_recording = False
                else:
                    wait_frames += 1
                    if wait_frames > max_wait_frames:
                        logger.error("No speech detected within 15 seconds")
                        is_recording = False
                    
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            is_recording = False

@app.on_event("startup")
async def startup_event():
    """Initialize models on startup"""
    global model, recognizer, vad_model
    try:
        model = load_vosk_model()
        recognizer = KaldiRecognizer(model, samplerate)
        vad_model = load_vad_model()
    except Exception as e:
        logger.error(f"Failed to initialize server: {str(e)}")
        raise

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
                
                try:
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
                    logger.error(f"Error in audio stream: {str(e)}")
                    await websocket.send_text(json.dumps({
                        "status": "error",
                        "error": str(e)
                    }))
                    
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        await websocket.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        if model is None or recognizer is None or vad_model is None:
            logger.error("Health check failed: models not initialized")
            return {"status": "unhealthy", "error": "Models not initialized"}
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)} 