import streamlit as st
import asyncio
import edge_tts
import re
import io
from pydub import AudioSegment

# --- កំណត់ទំព័រ ---
st.set_page_config(page_title="Khmer TTS Pro - លោកពូប៉ាវ", page_icon="🎙️")

# CSS សម្រួលសម្រស់វេបសាយ
st.markdown("""
    <style>
    .stTextArea textarea { font-size: 16px !important; border-radius: 10px; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #28a745; color: white; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

# --- មុខងារជំនួយ (Functions) ---

def parse_srt(srt_text):
    """បំបែក SRT ទៅជាបញ្ជីអត្ថបទ និងពេលវេលា"""
    pattern = r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\n$|$)"
    matches = re.findall(pattern, srt_text, re.DOTALL)
    subtitles = []
    for match in matches:
        start_time = match[1].replace(',', '.')
        h, m, s = start_time.split(':')
        start_ms = int(h)*3600000 + int(m)*60000 + float(s)*1000
        subtitles.append({"start_ms": start_ms, "text": match[3].replace('\n', ' ')})
    return subtitles

async def generate_audio(srt_text, voice, rate, pitch):
    """បង្កើតសំឡេងតាម SRT រួមបញ្ចូលជាមួយចន្លោះស្ងាត់"""
    subs = parse_srt(srt_text)
    combined_audio = AudioSegment.empty()
    current_ms = 0
    
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"

    for sub in subs:
        # បន្ថែមចន្លោះស្ងាត់
        silence_duration = sub['start_ms'] - current_ms
        if silence_duration > 0:
            combined_audio += AudioSegment.silent(duration=silence_duration)

        # បង្កើតសំឡេងពី Edge-TTS
        communicate = edge_tts.Communicate(sub['text'], voice, rate=rate_str, pitch=pitch_str)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        # បញ្ចូលសំឡេងទៅក្នុង Timeline
        segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
        combined_audio += segment
        current_ms = sub['start_ms'] + len(segment)

    buffer = io.BytesIO()
    combined_audio.export(buffer, format="mp3")
    return buffer.getvalue()

# --- ចំណុចប្រទាក់អ្នកប្រើ (UI) ---
st.title("🎙️ កម្មវិធីអានអត្ថបទខ្មែរតាមពេលវេលា")
st.write("បង្កើតឡើងដោយ៖ **លោកពូប៉ាវ**")

# កំណត់តួអង្គ និងសំឡេង
col_img, col_ctrl = st.columns([1, 2])

with col_img:
    voice_choice = st.selectbox("ជ្រើសរើសអ្នកអាន:", ["ស្រីមុំ (Sreymom)", "ពិសិដ្ឋ (Piseth)"])
    if "ស្រីមុំ" in voice_choice:
        voice_id, img_url = "km-KH-SreymomNeural", "https://cdn-icons-png.flaticon.com/512/6997/6997662.png"
    else:
        voice_id, img_url = "km-KH-PisethNeural", "https://cdn-icons-png.flaticon.com/512/4128/4128176.png"
    st.image(img_url, width=120)

with col_ctrl:
    speed = st.slider("ល្បឿនអាន (%):", -50, 50, 0, 5)
    pitch = st.slider("កម្រិតសំឡេង (Hz):", -20, 20, 0, 1)

# បញ្ចូលអត្ថបទ SRT
srt_input = st.text_area("បញ្ចូលទម្រង់ SRT (Timestamp):", height=250, 
                         placeholder="1\n00:00:01,000 --> 00:00:02,500\nសួស្តី ខ្ញុំឈ្មោះស្រីមុំ។")

if st.button("🔊 ចាប់ផ្តើមផលិតសំឡេង"):
    if srt_input.strip():
        with st.spinner("កំពុងដំណើរការ..."):
            try:
                final_audio = asyncio.run(generate_audio(srt_input, voice_id, speed, pitch))
                st.audio(final_audio, format="audio/mp3")
                st.download_button("📥 ទាញយក MP3", final_audio, "khmer_dubbing.mp3")
            except Exception as e:
                st.error(f"បញ្ហា៖ {e}\n(សូមប្រាកដថាបានដំឡើង FFmpeg រួចរាល់)")
    else:
        st.warning("សូមបញ្ចូលអត្ថបទ SRT ជាមុនសិន!")
