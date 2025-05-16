import asyncio
import websockets
import json

async def test_transcription():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        print("Connected to server. Starting transcription...")
        
        # Send start signal
        await websocket.send("start")
        
        # Wait for response
        response = await websocket.recv()
        result = json.loads(response)
        
        print("\nTranscription result:")
        print(f"Status: {result['status']}")
        print(f"Text: {result['transcription']}")

if __name__ == "__main__":
    asyncio.run(test_transcription()) 