import asyncio
import websockets
import json
import requests
import time
import sounddevice as sd
import logging

# Configure logging to only show errors and critical messages
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_health():
    """Test the health endpoint"""
    try:
        response = requests.get("http://localhost:8000/health")
        response.raise_for_status()
        health_data = response.json()
        
        if health_data["status"] == "healthy":
            return True
        else:
            logger.error(f"Health check failed: {health_data.get('error', 'Unknown error')}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Health check failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Health check failed with unexpected error: {str(e)}")
        return False

def list_audio_devices():
    """List available audio input devices"""
    try:
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        return input_devices
    except Exception as e:
        logger.error(f"Failed to list audio devices: {str(e)}")
        return []

def test_microphone():
    """Test if microphone is working"""
    try:
        with sd.InputStream(samplerate=16000, channels=1, dtype='int16') as stream:
            return True
    except Exception as e:
        logger.error(f"Microphone test failed: {str(e)}")
        return False

async def test_transcription_session(websocket, session_num):
    """Test a single transcription session"""
    print(f"\nStarting transcription session {session_num}...")
    print("Please speak into your microphone...")
    print("(You have 15 seconds to start speaking, then wait 2-3 seconds of silence to end)")
    
    try:
        # Send start signal
        await websocket.send("start")
        
        # Wait for response with timeout
        response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
        result = json.loads(response)
        
        print(f"\nSession {session_num} result:")
        print(f"Status: {result['status']}")
        
        if result["status"] == "error":
            logger.error(f"Session failed: {result.get('error', 'Unknown error')}")
            return False
            
        print(f"Text: {result['transcription']}")
        
        if not result["transcription"]:
            logger.error("No speech was detected or transcribed")
            return False
            
        return result["status"] == "complete" and result["transcription"]
    except asyncio.TimeoutError:
        logger.error("Session timed out - no speech detected")
        return False
    except Exception as e:
        logger.error(f"Session failed with error: {str(e)}")
        return False

async def run_tests():
    """Run all transcription tests"""
    if not await test_health():
        logger.error("Skipping transcription tests due to failed health check")
        return
    
    # List available audio devices
    input_devices = list_audio_devices()
    if not input_devices:
        logger.error("No audio input devices found!")
        return
    
    # Test default device
    try:
        default_device = sd.query_devices(kind='input')
        print(f"\nUsing default input device: {default_device['name']}")
    except Exception as e:
        logger.error(f"Failed to get default device: {str(e)}")
        return
    
    # Test microphone
    if not test_microphone():
        logger.error("Microphone test failed, please check your audio settings")
        return
    
    uri = "ws://localhost:8000/ws"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to server. Starting transcription tests...")
            
            # Test multiple sessions
            for i in range(3):
                success = await test_transcription_session(websocket, i + 1)
                if not success:
                    logger.error(f"Transcription session {i + 1} failed")
                    break
                print(f"✓ Transcription session {i + 1} completed")
                # Wait between sessions
                await asyncio.sleep(2)
                
    except websockets.exceptions.ConnectionClosed:
        logger.error("Connection to server was closed unexpectedly")
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")

if __name__ == "__main__":
    print("Starting Vosk API tests...")
    asyncio.run(run_tests())
    print("\nTests completed.") 