import os
import shutil
import logging
import mimetypes
import requests
import asyncio
import websockets
import json
import base64
import subprocess  # <--- NEW: Replaces pydub for audio conversion
from typing import List, Dict, Any
from abc import ABC, abstractmethod
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Google Imports
from google.cloud import speech
from google.genai import Client as GenAIClient
from google.genai import types 

# ─────────────────────────────────────────────────────────────────────────────
# 1) Configuration & Setup
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("AudioAgent")

app = FastAPI(title="Multi-Provider Transcription Agent")

# --- CREDENTIALS ---
PROJECT_ID = "sadproject2025"
LOCATION = "us-central1"
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "YOUR_SARVAM_KEY")
ORISTT_API_KEY = os.getenv("ORISTT_API_KEY", "YOUR_ORISTT_KEY")
ORISTT_URL_HOST = os.getenv("ORISTT_URL_HOST", "example.oriserve.com") 

# ─────────────────────────────────────────────────────────────────────────────
# 2) Abstract Interface
# ─────────────────────────────────────────────────────────────────────────────
class TranscriptionProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def transcribe(self, audio_path: str, mime_type: str) -> str:
        pass

# ─────────────────────────────────────────────────────────────────────────────
# 3) Provider 1: Google Cloud Speech-to-Text
# ─────────────────────────────────────────────────────────────────────────────
class GoogleSTTProvider(TranscriptionProvider):
    def __init__(self):
        self.client = speech.SpeechClient()

    @property
    def provider_name(self) -> str:
        return "Google_Cloud_STT"

    def transcribe(self, audio_path: str, mime_type: str) -> str:
        try:
            with open(audio_path, "rb") as audio_file:
                content = audio_file.read()
            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                language_code="en-US",
                enable_automatic_punctuation=True,
            )
            response = self.client.recognize(config=config, audio=audio)
            transcript = " ".join([result.alternatives[0].transcript for result in response.results])
            return transcript if transcript else "No speech detected."
        except Exception as e:
            logger.error(f"Google STT Error: {e}")
            return f"Error: {str(e)}"

# ─────────────────────────────────────────────────────────────────────────────
# 4) Provider 2: Google Gemini
# ─────────────────────────────────────────────────────────────────────────────
class GeminiAudioProvider(TranscriptionProvider):
    def __init__(self):
        self.client = GenAIClient(vertexai=True, project=PROJECT_ID, location=LOCATION)
        self.model_name = "gemini-2.0-flash-001" 

    @property
    def provider_name(self) -> str:
        return "Gemini_2.0_Multimodal"

    def transcribe(self, audio_path: str, mime_type: str) -> str:
        try:
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text="Transcribe this audio."),
                            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
                        ]
                    )
                ]
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini Error: {e}")
            return f"Error: {str(e)}"

# ─────────────────────────────────────────────────────────────────────────────
# 5) Provider 3: Sarvam AI
# ─────────────────────────────────────────────────────────────────────────────
class SarvamAIProvider(TranscriptionProvider):
    def __init__(self):
        self.api_key = SARVAM_API_KEY
        self.url = "https://api.sarvam.ai/speech-to-text"

    @property
    def provider_name(self) -> str:
        return "Sarvam_AI"

    def transcribe(self, audio_path: str, mime_type: str) -> str:
        if not self.api_key or "YOUR" in self.api_key: return "Error: API Key missing."
        try:
            headers = {"api-subscription-key": self.api_key}
            data = {"model": "saarika:v2.5", "language_code": "unknown"}
            with open(audio_path, 'rb') as f:
                files = {'file': (os.path.basename(audio_path), f, mime_type)}
                response = requests.post(self.url, headers=headers, data=data, files=files)
            if response.status_code == 200:
                return response.json().get("transcript", "No text.")
            return f"Error {response.status_code}: {response.text}"
        except Exception as e:
            logger.error(f"Sarvam Error: {e}")
            return f"Error: {str(e)}"

# ─────────────────────────────────────────────────────────────────────────────
# 6) Provider 4: OriSTT (WebSocket Streaming) -- UPDATED NO PYDUB
# ─────────────────────────────────────────────────────────────────────────────
class OriSTTProvider(TranscriptionProvider):
    def __init__(self):
        self.api_key = ORISTT_API_KEY
        self.host = ORISTT_URL_HOST.replace("wss://", "").replace("/", "")
        self.full_url = f"wss://{self.host}/connect?model=ori-prime-v2.3&sample_rate=16000&language=en"

    @property
    def provider_name(self) -> str:
        return "OriSTT_WebSocket"

    async def _stream_audio(self, audio_path: str):
        transcripts = []
        
        # --- NEW: Convert Audio to PCM 16kHz Mono using subprocess (ffmpeg) ---
        # This removes the dependency on pydub/audioop
        try:
            command = [
                'ffmpeg', 
                '-i', audio_path,       # Input file
                '-f', 's16le',          # Output format: Signed 16-bit Little Endian
                '-acodec', 'pcm_s16le', # Codec
                '-ar', '16000',         # Sample rate: 16kHz
                '-ac', '1',             # Channels: Mono
                '-v', 'quiet',          # Suppress logs
                'pipe:1'                # Output to stdout
            ]
            
            # Run the command and capture output bytes
            process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if process.returncode != 0:
                logger.error(f"FFmpeg Error: {process.stderr.decode()}")
                return f"FFmpeg Conversion Failed. Is ffmpeg installed?"
                
            raw_data = process.stdout
            
        except FileNotFoundError:
            return "Error: FFmpeg is not installed on the system."
        except Exception as e:
            return f"Error processing audio: {e}"

        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            async with websockets.connect(self.full_url, additional_headers=headers) as ws:
                logger.info("Connected to OriSTT WebSocket")
                
                CHUNK_SIZE = 320 # 10ms for 16kHz
                offset = 0
                
                async def sender():
                    nonlocal offset
                    while offset < len(raw_data):
                        chunk = raw_data[offset : offset + CHUNK_SIZE]
                        offset += CHUNK_SIZE
                        payload = {"audio": base64.b64encode(chunk).decode("utf-8")}
                        await ws.send(json.dumps(payload))
                        await asyncio.sleep(0.01)
                    await asyncio.sleep(1)

                async def receiver():
                    try:
                        while True:
                            msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                            data = json.loads(msg)
                            if data.get("status") == "recognized":
                                text = data.get("data", "")
                                if text: transcripts.append(text)
                    except asyncio.TimeoutError: pass
                    except Exception: pass

                await asyncio.gather(sender(), receiver())

        except Exception as e:
            logger.error(f"OriSTT Connection failed: {e}")
            return f"Connection Error: {str(e)}"

        return " ".join(transcripts)

    def transcribe(self, audio_path: str, mime_type: str) -> str:
        if not self.api_key or "YOUR" in self.api_key: return "Error: OriSTT API Key missing."
        try:
            return asyncio.run(self._stream_audio(audio_path))
        except Exception as e:
            return f"Runtime Error: {str(e)}"

# ─────────────────────────────────────────────────────────────────────────────
# 7) The Agent
# ─────────────────────────────────────────────────────────────────────────────
class TranscriptionAgent:
    def __init__(self):
        self.providers: List[TranscriptionProvider] = [
            GoogleSTTProvider(),
            GeminiAudioProvider(),
            SarvamAIProvider(),
            OriSTTProvider()
        ]

    def process_audio(self, file_path: str, filename: str) -> Dict[str, Any]:
        results = {}
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type: mime_type = "audio/mpeg"
        
        logger.info(f"Processing file: {filename} ({mime_type})")

        for provider in self.providers:
            logger.info(f"Running: {provider.provider_name}")
            text = provider.transcribe(file_path, mime_type)
            results[provider.provider_name] = text
            
        return results

agent = TranscriptionAgent()

# ─────────────────────────────────────────────────────────────────────────────
# 8) Endpoints
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/upload-audio/")
async def upload_audio(file: UploadFile = File(...)):
    temp_filename = f"temp_{file.filename}"
    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        transcription_results = agent.process_audio(temp_filename, file.filename)
        
        if os.path.exists(temp_filename): os.remove(temp_filename)
        return JSONResponse(content={"filename": file.filename, "transcriptions": transcription_results})
    except Exception as e:
        if os.path.exists(temp_filename): os.remove(temp_filename)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)