import streamlit as st
import requests

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────
BACKEND_URL = "http://localhost:8000/upload-audio/"

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
    model_option = st.selectbox(
        "Choose Transcription Model",
        (
            "Compare All Models",
            "Gemini 2.0 Flash (Multimodal)",
            "Google Standard STT", 
            "Sarvam AI (Indian Langs)"
        )
    )

    st.divider()
    process_btn = st.button("🚀 Transcribe Audio", type="primary", use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# Main Page: Results
# ─────────────────────────────────────────────────────────────────────────────
st.title("🎙️ AI Audio Agent")
st.markdown("Upload your audio file in the sidebar to generate text using **Google** and **Sarvam AI**.")

if process_btn:
    if uploaded_file is None:
        st.error("⚠️ Please upload an audio file first!")
    else:
        with st.spinner("Processing audio... Sending to API Agents..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                response = requests.post(BACKEND_URL, files=files)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("transcriptions", {})
                    st.success("✅ Transcription Complete!")

                    # ─── DISPLAY LOGIC ───
                    
                    if model_option == "Gemini 2.0 Flash (Multimodal)":
                        st.subheader("✨ Gemini 2.0 Flash Result")
                        st.markdown(results.get('Gemini_2.0_Multimodal', 'No result found.'))

                    elif model_option == "Google Standard STT":
                        st.subheader("☁️ Google Cloud STT Result")
                        st.markdown(results.get('Google_Cloud_STT', 'No result found.'))

                    elif model_option == "Sarvam AI (Indian Langs)":
                        st.subheader("🇮🇳 Sarvam AI Result")
                        st.markdown(results.get('Sarvam_AI', 'No result found.'))

                    else: # Compare All
                        st.subheader("⚖️ Model Comparison")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.markdown("### ✨ Gemini 2.0")
                            st.text_area("GenAI", value=results.get('Gemini_2.0_Multimodal', ''), height=300)
                        
                        with col2:
                            st.markdown("### ☁️ Google STT")
                            st.text_area("Standard STT", value=results.get('Google_Cloud_STT', ''), height=300)

                        with col3:
                            st.markdown("### 🇮🇳 Sarvam AI")
                            st.text_area("Sarvam", value=results.get('Sarvam_AI', ''), height=300)

                else:
                    st.error(f"Backend Error: {response.text}")

            except requests.exceptions.ConnectionError:
                st.error("🚨 Could not connect to Backend. Is it running?")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

else:
    if not uploaded_file:
        st.info("👈 Please upload a file in the sidebar to get started.")