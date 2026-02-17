# AI Audio Agent - Multi-Provider Speech-to-Text Transcription

A full-stack web application that provides audio transcription capabilities using multiple AI providers: **Google Cloud Speech-to-Text**, **Gemini 2.0 Flash**, **Sarvam AI**, and **OriSTT**. This tool allows you to compare transcription results across different providers with support for multiple audio formats and languages.

## Features

- **Multiple Transcription Providers**
  - Google Cloud Speech-to-Text (Standard STT)
  - Gemini 2.0 Flash (Multimodal AI)
  - Sarvam AI (Indian Languages Support)
  - OriSTT (Real-time WebSocket-based)

- **Model Comparison**: Upload once and compare transcription results across all providers simultaneously

- **Supported Audio Formats**: MP3, WAV, FLAC, M4A (up to 200MB per file)

- **User-Friendly Interface**: Built with Streamlit for intuitive audio upload and results visualization

- **Real-time Processing**: Streaming transcription results from multiple providers

## Project Structure

```
DemoSTTtester/
├── backend/
│   ├── main.py              # FastAPI server with transcription logic
│   ├── requirements.txt      # Python dependencies
│   └── .env                  # Configuration (API keys & credentials)
├── frontend/
│   ├── main.py              # Streamlit UI application
│   └── requirements.txt      # Frontend dependencies
├── venv/                     # Python virtual environment
└── README.md                 # This file
```

## Installation

### Prerequisites

- Python 3.8+
- pip package manager
- Virtual environment (recommended)

### Setup

1. **Clone or navigate to the project directory**
   ```bash
   cd DemoSTTtester
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install backend dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Install frontend dependencies**
   ```bash
   cd ../frontend
   pip install -r requirements.txt
   ```

5. **Configure environment variables**
   
   Create a `.env` file in the `backend/` directory with your API credentials:
   ```bash
   cd ../backend
   cat > .env << 'EOF'
   SARVAM_API_KEY=your_sarvam_api_key_here
   ORISTT_API_KEY=your_oristt_api_key_here
   ORISTT_URL_HOST=ori-asr-test.oriserve.com
   EOF
   ```

   **Required API Keys:**
   - **Google Cloud**: Set up Application Default Credentials (see [Google Cloud Setup](#google-cloud-setup))
   - **Sarvam AI**: Get your API key from [Sarvam AI](https://sarvam.ai/)
   - **OriSTT**: Get credentials from [OriServe](https://oriserve.com/)

## Google Cloud Setup

1. **Create a Google Cloud Project**
   ```bash
   gcloud projects create sadproject2025
   gcloud config set project sadproject2025
   ```

2. **Enable Required APIs**
   ```bash
   gcloud services enable speech.googleapis.com
   gcloud services enable aiplatform.googleapis.com
   ```

3. **Create a Service Account**
   ```bash
   gcloud iam service-accounts create audio-agent
   gcloud projects add-iam-policy-binding sadproject2025 \
     --member=serviceAccount:audio-agent@sadproject2025.iam.gserviceaccount.com \
     --role=roles/aiplatform.user
   ```

4. **Generate and Set Credentials**
   ```bash
   gcloud iam service-accounts keys create ~/google-credentials.json \
     --iam-account=audio-agent@sadproject2025.iam.gserviceaccount.com
   
   export GOOGLE_APPLICATION_CREDENTIALS=~/google-credentials.json
   ```

## Running the Application

### Terminal 1: Start Backend Server

```bash
cd backend
python3 main.py
```

Or with Uvicorn directly:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The backend API will be available at `http://localhost:8000`

### Terminal 2: Start Frontend UI

```bash
cd frontend
streamlit run main.py
```

The Streamlit UI will open automatically at `http://localhost:8501`

## Usage

1. **Open the Frontend** - Navigate to `http://localhost:8501` in your browser

2. **Upload Audio File**
   - Click "Browse files" in the sidebar
   - Select an audio file (MP3, WAV, FLAC, or M4A)
   - File size limit: 200MB

3. **Select Transcription Model**
   - **Compare All Models**: Run transcription on all providers simultaneously
   - **Gemini 2.0 Flash**: Google's multimodal AI model
   - **Google Standard STT**: Google Cloud's speech recognition
   - **Sarvam AI**: Specialized for Indian languages
   - **OriSTT**: Real-time WebSocket-based transcription

4. **Transcribe Audio**
   - Click the "Transcribe Audio" button
   - Wait for results from selected providers
   - View and compare transcriptions

## API Endpoints

### Backend API (FastAPI)

**POST** `/upload-audio/`
- Upload an audio file for transcription
- **Parameters**: `file` (FormData - audio file)
- **Returns**: JSON with transcription results from all providers

**Example cURL**:
```bash
curl -X POST "http://localhost:8000/upload-audio/" \
  -F "file=@your_audio_file.mp3"
```

## Architecture

### Backend (`backend/main.py`)

- **FastAPI Server**: RESTful API for audio processing
- **Abstract Interface**: `TranscriptionProvider` base class for provider implementations
- **Provider Implementations**: Separate classes for each transcription service
- **Audio Processing**: Format conversion and optimization
- **Async/Concurrent**: Processes multiple providers in parallel

### Frontend (`frontend/main.py`)

- **Streamlit App**: Interactive web UI
- **File Upload**: Drag-and-drop or browse file selection
- **Model Selection**: Dropdown to choose transcription providers
- **Results Display**: Side-by-side comparison of transcriptions
- **Status Indicators**: Real-time progress updates

## Supported Languages

- **Google Cloud Speech**: 125+ languages
- **Gemini 2.0 Flash**: 100+ languages
- **Sarvam AI**: Hindi, Tamil, Telugu, Kannada, Malayalam, English
- **OriSTT**: English and other configurable languages

## Error Handling

The application includes comprehensive error handling:

- Missing audio files
- Invalid API credentials
- Network connectivity issues
- WebSocket connection errors (OriSTT)
- File format validation
- API rate limit handling

## Performance Considerations

- **Parallel Processing**: All providers are queried simultaneously
- **Audio Optimization**: Files are converted to optimal formats for each provider
- **Streaming Results**: Results are streamed to the UI as they complete
- **Connection Pooling**: Efficient HTTP and WebSocket connection management

## Troubleshooting

### Issue: "ScriptRunContext" warnings from Streamlit
- **Cause**: Running Python directly instead of with streamlit
- **Solution**: Always use `streamlit run main.py` to start the frontend

### Issue: Backend API not responding
- **Solution**: Ensure backend is running on `http://localhost:8000`
- Check that all dependencies in `backend/requirements.txt` are installed

### Issue: Google Cloud authentication error
- **Solution**: Verify `GOOGLE_APPLICATION_CREDENTIALS` environment variable is set correctly
- Check that the service account has required IAM roles

### Issue: OriSTT connection error
- **Solution**: Verify `ORISTT_URL_HOST` is set correctly in `.env`
- Check network connectivity to OriServe endpoint

### Issue: Sarvam API key invalid
- **Solution**: Verify `SARVAM_API_KEY` in `.env` file
- Check API key hasn't expired on Sarvam AI dashboard

## Dependencies

### Backend
- `fastapi>=0.109.0` - Web framework
- `uvicorn[standard]>=0.27.0` - ASGI server
- `google-cloud-speech>=2.21.0` - Google Speech API
- `google-genai>=0.3.0` - Gemini API
- `requests>=2.31.0` - HTTP library for Sarvam AI
- `websockets>=12.0` - WebSocket support for OriSTT
- `python-dotenv>=1.0.0` - Environment variable management

### Frontend
- `streamlit` - Web UI framework
- `requests` - HTTP client library

## Development

### Adding a New Provider

1. Create a new class inheriting from `TranscriptionProvider` in `backend/main.py`
2. Implement the `provider_name` property and `transcribe()` method
3. Add provider initialization in the main FastAPI endpoint
4. Update `frontend/main.py` to include the new option in the model selector

### Logging

The application uses Python's standard `logging` module. Check logs for debugging:
```bash
# Backend logs appear in the terminal where you ran main.py
# Frontend logs appear in Streamlit's terminal
```

## License

This project is provided as-is for demonstration and testing purposes.

## Support

For issues or questions regarding specific providers:
- **Google Cloud**: [Cloud Support](https://cloud.google.com/support)
- **Sarvam AI**: [Sarvam Documentation](https://sarvam.ai/docs)
- **OriSTT**: [OriServe Support](https://oriserve.com/)

---

**Happy Transcribing!** 🎙️
