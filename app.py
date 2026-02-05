import streamlit as st
import asyncio
import edge_tts

# --- កំណត់ទំព័រ ---
st.set_page_config(page_title="Khmer TTS - លោកពូប៉ាវ", page_icon="🎙️", layout="centered")

# --- CSS សម្រាប់រចនាប័ទ្មបន្ថែម ---
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stTextArea textarea { font-size: 18px !important; border-radius: 15px; }
    .stButton>button { 
        background-color: #007bff; color: white; border-radius: 10px; 
        font-family: 'Kantumruy Pro'; height: 3.5em; font-size: 18px;
    }
    .speaker-card {
        padding: 15px; background: white; border-radius: 15px;
        text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

async def generate_full_audio(text, voice, rate, pitch):
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"
    communicate = edge_tts.Communicate(text, voice, rate=rate_str, pitch=pitch_str)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- ចំណុចប្រទាក់អ្នកប្រើ (UI) ---
st.title("🎙️ កម្មវិធីអានអត្ថបទជាភាសាខ្មែរ AI")
st.markdown("<h4 style='text-align: center; color: gray;'>សម្រួលបច្ចេកទេសដោយ៖ លោកពូប៉ាវ</h4>", unsafe_allow_html=True)

# ផ្នែកបង្ហាញតួអង្គ
col_img, col_ctrl = st.columns([1, 2])

with col_img:
    voice_choice = st.selectbox("ជ្រើសរើសអ្នកអាន:", ["ស្រីមុំ (Sreymom)", "ពិសិដ្ឋ (Piseth)"])
    
    # បង្ហាញរូបភាពតំណាងតាមតួអង្គ
    if "ស្រីមុំ" in voice_choice:
        voice_id = "km-KH-SreymomNeural"
        st.image("https://cdn-icons-png.flaticon.com/512/6997/6997662.png", width=150, caption="កញ្ញា ស្រីមុំ")
    else:
        voice_id = "km-KH-PisethNeural"
        st.image("https://cdn-icons-png.flaticon.com/512/4128/4128176.png", width=150, caption="លោក ពិសិដ្ឋ")

with col_ctrl:
    speed = st.slider("ល្បឿនអាន (%):", -50, 50, 0, 5)
    pitch = st.slider("កម្រិតសំឡេង (Hz):", -20, 20, 0, 1)

# ប្រអប់បញ្ចូលអត្ថបទ
text_input = st.text_area("✍️ បញ្ចូលអត្ថបទខ្មែរ៖", height=200, placeholder="សរសេរអត្ថបទដែលអ្នកចង់ឱ្យ AI អាននៅទីនេះ...")

# ប៊ូតុងដំណើរការ
if st.button("🔊 ចាប់ផ្តើមបំប្លែង និងស្ដាប់សំឡេង"):
    if text_input.strip():
        with st.spinner("កំពុងដំណើរការ..."):
            try:
                audio_bytes = asyncio.run(generate_full_audio(text_input, voice_id, speed, pitch))
                st.success("រួចរាល់!")
                st.audio(audio_bytes, format="audio/mp3")
                
                st.download_button(
                    label="📥 ទាញយកឯកសារសំឡេង (MP3)",
                    data=audio_bytes,
                    file_name=f"{voice_choice}_audio.mp3",
                    mime="audio/mp3"
                )
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("សូមបញ្ចូលអត្ថបទជាមុនសិន!")
