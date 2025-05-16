# Vosk Speech Recognition Toolkit

Vosk is an offline open source speech recognition toolkit. It enables
speech recognition for 20+ languages and dialects - English, Indian
English, German, French, Spanish, Portuguese, Chinese, Russian, Turkish,
Vietnamese, Italian, Dutch, Catalan, Arabic, Greek, Farsi, Filipino,
Ukrainian, Kazakh, Swedish, Japanese, Esperanto, Hindi, Czech, Polish.
More to come.

Vosk models are small (50 Mb) but provide continuous large vocabulary
transcription, zero-latency response with streaming API, reconfigurable
vocabulary and speaker identification.

Speech recognition bindings implemented for various programming languages
like Python, Java, Node.JS, C#, C++, Rust, Go and others.

Vosk supplies speech recognition for chatbots, smart home appliances,
virtual assistants. It can also create subtitles for movies,
transcription for lectures and interviews.

Vosk scales from small devices like Raspberry Pi or Android smartphone to
big clusters.

# Documentation

For installation instructions, examples and documentation visit [Vosk
Website](https://alphacephei.com/vosk).

# Spanish Voice Transcription API

This is a FastAPI service that provides real-time Spanish voice transcription using Vosk and Silero VAD for voice activity detection.

## Features

- Real-time Spanish voice transcription
- Voice Activity Detection (VAD) using Silero
- WebSocket interface for streaming transcription
- Automatic detection of speech end
- Health check endpoint

## Prerequisites

- Python 3.8+
- Vosk Spanish model
- Microphone access

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Download the Vosk Spanish model:
```bash
wget https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip
unzip vosk-model-small-es-0.42.zip
mv vosk-model-small-es-0.42 model
```

## Usage

1. Start the server:
```bash
uvicorn app:app --reload
```

2. Connect to the WebSocket endpoint at `ws://localhost:8000/ws`

3. Send "start" message to begin transcription

4. The service will:
   - Start recording from the microphone
   - Transcribe Spanish speech in real-time
   - Detect when speech ends using Silero VAD
   - Send the complete transcription when done

5. The response will be in JSON format:
```json
{
    "status": "complete",
    "transcription": "your transcribed text here"
}
```

## API Endpoints

- `GET /health`: Health check endpoint
- `WS /ws`: WebSocket endpoint for real-time transcription

## Notes

- The service uses a 16kHz sample rate
- Voice activity detection threshold is set to 0.5
- The service automatically stops recording when silence is detected after speech
