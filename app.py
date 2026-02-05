import streamlit as st
import asyncio
import edge_tts
import io

# --- កំណត់ទំព័រ ---
st.set_page_config(page_title="Khmer Text-to-Speech", page_icon="🎙️")

# CSS សម្រាប់រចនាប័ទ្ម
st.markdown("""
    <style>
    .stTextArea textarea { font-size: 18px !important; line-height: 1.6; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #28a745; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- មុខងារបង្កើតសំឡេង (កែសម្រួលបន្ថែម Rate និង Pitch) ---
async def generate_full_audio(text, voice, rate, pitch):
    # បំប្លែងតម្លៃទៅជា Format ដែល edge-tts យល់ (ឧទាហរណ៍៖ "+0%", "+0Hz")
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"
    
    communicate = edge_tts.Communicate(text, voice, rate=rate_str, pitch=pitch_str)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- ចំណុចប្រទាក់អ្នកប្រើ (UI) ---
st.title("🎙️ កម្មវិធីអានអត្ថបទជាភាសាខ្មែរ")
st.subheader("បង្កើតឡើងដោយលោកពូប៉ាវ")

# ប្លុកកំណត់សំឡេង
with st.expander("🛠️ ការកំណត់សំឡេងបន្ថែម", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        voice_choice = st.selectbox("ជ្រើសរើសអ្នកអាន:", ["ស្រីមុំ (Sreymom)", "ពិសិដ្ឋ (Piseth)"])
        voice_id = "km-KH-SreymomNeural" if "ស្រីមុំ" in voice_choice else "km-KH-PisethNeural"
    
    with col2:
        # Slider សម្រាប់ល្បឿន និង កម្រិតសំឡេង
        speed = st.slider("ល្បឿនអាន (%):", min_value=-50, max_value=50, value=0, step=5)
        pitch = st.slider("កម្រិតសំឡេង (Hz):", min_value=-20, max_value=20, value=0, step=1)

# ប្រអប់បញ្ចូលអត្ថបទ
text_input = st.text_area("សរសេរអត្ថបទនៅទីនេះ:", height=250, placeholder="ឧទាហរណ៍៖ សួស្តី! ខ្ញុំបាទឈ្មោះពិសិដ្ឋ រីករាយដែលបានជួបអ្នក។")

if st.button("🔊 ចាប់ផ្តើមបំប្លែងជាសំឡេង"):
    if text_input.strip():
        with st.spinner("កំពុងបង្កើតសំឡេង សូមរង់ចាំ..."):
            try:
                # បញ្ជូនតម្លៃ speed និង pitch ទៅក្នុង function
                audio_bytes = asyncio.run(generate_full_audio(text_input, voice_id, speed, pitch))
                
                st.success("✅ ការបំប្លែងជោគជ័យ!")
                st.audio(audio_bytes, format="audio/mp3")
                
                st.download_button(
                    label="📥 ទាញយកជាឯកសារ MP3",
                    data=audio_bytes,
                    file_name="khmer_audio_custom.mp3",
                    mime="audio/mp3"
                )
            except Exception as e:
                st.error(f"មានបញ្ហាបច្ចេកទេស៖ {e}")
    else:
        st.warning("សូមបញ្ចូលអត្ថបទជាមុនសិន!")
