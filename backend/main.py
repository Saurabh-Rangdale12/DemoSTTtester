import os
import shutil
import logging
import mimetypes
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

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("AudioAgent")

app = FastAPI(title="Multi-Provider Transcription Agent")

# --- FIX 1: Hardcoded Credentials to stop the "Warning" ---
PROJECT_ID = "sadproject2025"
LOCATION = "us-central1"

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
# 3) Provider 1: Google Cloud Speech-to-Text (Standard STT)
# ─────────────────────────────────────────────────────────────────────────────
class GoogleSTTProvider(TranscriptionProvider):
    def __init__(self):
        # ADC: Automatically uses credentials from 'gcloud auth application-default login'
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

            logger.info("Sending to Google Cloud STT...")
            response = self.client.recognize(config=config, audio=audio)

            transcript = " ".join([result.alternatives[0].transcript for result in response.results])
            return transcript if transcript else "No speech detected."
        except Exception as e:
            logger.error(f"Google STT Error: {e}")
            return f"Error: {str(e)}"

# ─────────────────────────────────────────────────────────────────────────────
# 4) Provider 2: Google Gen AI (Gemini Multimodal)
# ─────────────────────────────────────────────────────────────────────────────
class GeminiAudioProvider(TranscriptionProvider):
    def __init__(self):
        # --- FIX 2: Added 'vertexai=True' ---
        # The SDK requires this flag to know we are using Google Cloud (ADC)
        # instead of an API Key.
        self.client = GenAIClient(
            vertexai=True, 
            project=PROJECT_ID, 
            location=LOCATION
        )
        self.model_name = "gemini-2.0-flash-001" 

    @property
    def provider_name(self) -> str:
        return "Gemini_2.0_Multimodal"

    def transcribe(self, audio_path: str, mime_type: str) -> str:
        try:
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
            
            logger.info(f"Sending to Gemini 2.0 ({mime_type})...")
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text="Please transcribe this audio file exactly as spoken."),
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
# 5) The Agent / Orchestrator
# ─────────────────────────────────────────────────────────────────────────────
class TranscriptionAgent:
    def __init__(self):
        self.providers: List[TranscriptionProvider] = [
            GoogleSTTProvider(),
            GeminiAudioProvider()
        ]

    def process_audio(self, file_path: str, filename: str) -> Dict[str, Any]:
        results = {}
        
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            mime_type = "audio/mpeg" 
            
        logger.info(f"Processing file: {filename} detected as {mime_type}")

        for provider in self.providers:
            logger.info(f"Running provider: {provider.provider_name}")
            text = provider.transcribe(file_path, mime_type)
            results[provider.provider_name] = text
            
        return results

agent = TranscriptionAgent()

# ─────────────────────────────────────────────────────────────────────────────
# 6) API Endpoints
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/upload-audio/")
async def upload_audio(file: UploadFile = File(...)):
    temp_filename = f"temp_{file.filename}"
    
    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        transcription_results = agent.process_audio(temp_filename, file.filename)
        
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

        return JSONResponse(content={
            "filename": file.filename,
            "transcriptions": transcription_results
        })

    except Exception as e:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def home():
    return {"message": "Audio Agent is Running (Authenticated via GCloud CLI)"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)