import streamlit as st
import requests

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────
BACKEND_URL = "http://localhost:8000/upload-audio/"

# Set page layout
st.set_page_config(
    page_title="AI Audio Transcriber",
    page_icon="🎙️",
    layout="wide"
)

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar: Controls
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🎛️ Control Panel")
    
    st.write("### 1. Upload File")
    uploaded_file = st.file_uploader(
        "Choose an audio file...", 
        type=['mp3', 'wav', 'flac', 'm4a']
    )

    st.write("### 2. Select Model")
    # The dropdown you requested
    model_option = st.selectbox(
        "Choose Transcription Model",
        (
            "Gemini 2.0 Flash (Multimodal)",
            "Google Standard STT", 
            "Compare All Models"  # Option to see both side-by-side
        )
    )

    st.divider()
    
    # Process Button
    process_btn = st.button("🚀 Transcribe Audio", type="primary", use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# Main Page: Results
# ─────────────────────────────────────────────────────────────────────────────
st.title("🎙️ AI Audio Agent")
st.markdown("Upload your audio file in the sidebar to generate text using Google's latest AI models.")

if process_btn:
    if uploaded_file is None:
        st.error("⚠️ Please upload an audio file first!")
    else:
        # Show a loading spinner while talking to the backend
        with st.spinner("Processing audio... Sending to Google Cloud..."):
            try:
                # Prepare the file for upload
                files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                
                # Send to FastAPI Backend
                response = requests.post(BACKEND_URL, files=files)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("transcriptions", {})

                    st.success("✅ Transcription Complete!")

                    # ─── DISPLAY LOGIC BASED ON DROPDOWN ───
                    
                    # Option 1: Gemini Only
                    if model_option == "Gemini 2.0 Flash (Multimodal)":
                        st.subheader("✨ Gemini 2.0 Flash Result")
                        st.info("Using Multimodal Generative AI")
                        st.markdown(f"**Transcript:**\n\n{results.get('Gemini_2.0_Multimodal', 'No result found.')}")

                    # Option 2: Google Standard STT Only
                    elif model_option == "Google Standard STT":
                        st.subheader("☁️ Google Cloud STT Result")
                        st.info("Using Standard Speech-to-Text API")
                        st.markdown(f"**Transcript:**\n\n{results.get('Google_Cloud_STT', 'No result found.')}")

                    # Option 3: Compare All
                    else:
                        st.subheader("⚖️ Model Comparison")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("### ✨ Gemini 2.0")
                            st.text_area("GenAI Output", value=results.get('Gemini_2.0_Multimodal', ''), height=300)
                        
                        with col2:
                            st.markdown("### ☁️ Google STT")
                            st.text_area("Standard STT Output", value=results.get('Google_Cloud_STT', ''), height=300)

                else:
                    st.error(f"Backend Error: {response.text}")

            except requests.exceptions.ConnectionError:
                st.error("🚨 Could not connect to Backend. Is it running? (Run `python backend_agent.py`)")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

else:
    # Initial State Placeholder
    if not uploaded_file:
        st.info("👈 Please upload a file in the sidebar to get started.")