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
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🎛️ Control Panel")
    
    st.write("### 1. Upload File")
    uploaded_file = st.file_uploader("Choose an audio file...", type=['mp3', 'wav', 'flac', 'm4a'])

    st.write("### 2. Select Model")
    model_option = st.selectbox(
        "Choose Transcription Model",
        (
            "Compare All Models",
            "Gemini 2.0 Flash (Multimodal)",
            "Google Standard STT", 
            "Sarvam AI (Indian Langs)",
            "OriSTT (Real-time WS)"
        )
    )

    st.divider()
    process_btn = st.button("🚀 Transcribe Audio", type="primary", use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# Main Page
# ─────────────────────────────────────────────────────────────────────────────
st.title("🎙️ AI Audio Agent")
st.markdown("Upload your audio file in the sidebar to generate text using **Google**, **Sarvam**, and **OriSTT**.")

if process_btn:
    if uploaded_file is None:
        st.error("⚠️ Please upload an audio file first!")
    else:
        with st.spinner("Processing... Streaming to Providers..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                response = requests.post(BACKEND_URL, files=files)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("transcriptions", {})
                    st.success("✅ Transcription Complete!")

                    # ─── LOGIC ───
                    
                    if model_option == "Gemini 2.0 Flash (Multimodal)":
                        st.subheader("✨ Gemini 2.0 Flash")
                        st.markdown(results.get('Gemini_2.0_Multimodal', 'No result.'))

                    elif model_option == "Google Standard STT":
                        st.subheader("☁️ Google Cloud STT")
                        st.markdown(results.get('Google_Cloud_STT', 'No result.'))

                    elif model_option == "Sarvam AI (Indian Langs)":
                        st.subheader("🇮🇳 Sarvam AI")
                        st.markdown(results.get('Sarvam_AI', 'No result.'))

                    elif model_option == "OriSTT (Real-time WS)":
                        st.subheader("📡 OriSTT (WebSocket)")
                        st.markdown(results.get('OriSTT_WebSocket', 'No result.'))

                    else: # Compare All
                        st.subheader("⚖️ Model Comparison")
                        col1, col2 = st.columns(2)
                        col3, col4 = st.columns(2)
                        
                        with col1:
                            st.markdown("### ✨ Gemini 2.0")
                            st.text_area("GenAI", value=results.get('Gemini_2.0_Multimodal', ''), height=200)
                        
                        with col2:
                            st.markdown("### ☁️ Google STT")
                            st.text_area("Standard STT", value=results.get('Google_Cloud_STT', ''), height=200)

                        with col3:
                            st.markdown("### 🇮🇳 Sarvam AI")
                            st.text_area("Sarvam", value=results.get('Sarvam_AI', ''), height=200)

                        with col4:
                            st.markdown("### 📡 OriSTT")
                            st.text_area("OriSTT WebSocket", value=results.get('OriSTT_WebSocket', ''), height=200)

                else:
                    st.error(f"Backend Error: {response.text}")

            except requests.exceptions.ConnectionError:
                st.error("🚨 Could not connect to Backend.")
            except Exception as e:
                st.error(f"Error: {e}")

else:
    if not uploaded_file:
        st.info("👈 Please upload a file in the sidebar.")