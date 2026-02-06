import streamlit as st
import asyncio
import edge_tts
import re
import io
from pydub import AudioSegment

# --- កំណត់ទំព័រ ---
st.set_page_config(page_title="Khmer TTS Pro - លោកពូប៉ាវ", page_icon="🎙️")

# ស្ទីល UI ឱ្យមើលទៅស្អាត និងងាយស្រួលប្រើ
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stTextArea textarea { font-size: 16px !important; border: 2px solid #2ecc71; border-radius: 10px; }
    .stButton>button { background-color: #2ecc71; color: white; border-radius: 10px; font-weight: bold; width: 100%; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

# --- មុខងារបំបែកអត្ថបទ SRT យកតែ Start Time ---
def parse_srt(srt_text):
    # Pattern សម្រាប់ចាប់យកលេខរៀង ម៉ោងចាប់ផ្តើម និងអត្ថបទ
    pattern = r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\n$|$)"
    matches = re.findall(pattern, srt_text, re.DOTALL)
    
    subtitles = []
    def to_ms(time_str):
        time_str = time_str.replace(',', '.')
        h, m, s = time_str.split(':')
        return int(h)*3600000 + int(m)*60000 + float(s)*1000

    for match in matches:
        subtitles.append({
            "start_ms": to_ms(match[1]),
            "text": match[3].strip()
        })
    return subtitles

# --- មុខងារផលិតសំឡេងតាមលំដាប់ម៉ោង (Strict Position) ---
async def generate_audio(srt_text, voice, rate, pitch):
    subs = parse_srt(srt_text)
    if not subs:
        return None

    # ១. បង្កើត Timeline ស្ងាត់មួយជាមុនសិន ដែលមានរយៈពេលវែងល្មម
    # យើងយកម៉ោងចាប់ផ្តើមចុងក្រោយ + ១០ វិនាទី ដើម្បីការពារការដាច់កន្ទុយ
    total_duration_ms = subs[-1]['start_ms'] + 10000 
    final_combined = AudioSegment.silent(duration=total_duration_ms)
    
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"

    for sub in subs:
        # ២. បង្កើតសំឡេង AI សម្រាប់ឃ្លានីមួយៗ
        communicate = edge_tts.Communicate(sub['text'], voice, rate=rate_str, pitch=pitch_str)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
        
        # ៣. ដាក់សំឡេងចូលក្នុង Timeline តាមទីតាំងម៉ោង (Position) ច្បាស់លាស់
        # វិធីនេះនឹងធ្វើឱ្យវានិយាយចំពេល Start Time ជានិច្ច ទោះបីជាឃ្លាមុនអានជាន់គ្នាក៏ដោយ
        final_combined = final_combined.overlay(segment, position=sub['start_ms'])

    # កាត់ផ្នែកស្ងាត់ដែលនៅសល់កន្ទុយចោល ដើម្បីឱ្យ File តូចល្មម
    # រកមើលកន្លែងដែលសំឡេងចប់ពិតប្រាកដ
    final_combined = final_combined.strip_silence(silence_thresh=-50, padding=100)

    buffer = io.BytesIO()
    final_combined.export(buffer, format="mp3")
    return buffer.getvalue()

# --- ចំណុចប្រទាក់អ្នកប្រើ (UI) ---
st.title("🎙️ Khmer SRT Audio (Strict Sync V3)")
st.write("ជំនាន់កែសម្រួល៖ បង្ខំឱ្យអានចំម៉ោង Start Time ១០០%")

col1, col2 = st.columns([1, 2])

with col1:
    voice_choice = st.selectbox("ជ្រើសរើសអ្នកអាន:", ["ស្រីមុំ (Sreymom)", "ពិសិដ្ឋ (Piseth)"])
    voice_id = "km-KH-SreymomNeural" if "ស្រីមុំ" in voice_choice else "km-KH-PisethNeural"
    img_url = "https://cdn-icons-png.flaticon.com/512/6997/6997662.png" if "ស្រីមុំ" in voice_choice else "https://cdn-icons-png.flaticon.com/512/4128/4128176.png"
    st.image(img_url, width=120)

with col2:
    speed = st.slider("ល្បឿនអាន (%):", -50, 50, 0, 5)
    pitch = st.slider("កម្រិតសំឡេង (Hz):", -20, 20, 0, 1)

srt_input = st.text_area("បញ្ចូលទម្រង់ SRT នៅទីនេះ:", height=250, 
                         placeholder="1\n00:00:01,000 --> 00:00:02,000\nសួស្តីបងប្អូន...")

if st.button("🔊 ចាប់ផ្តើមផលិតសំឡេង"):
    if srt_input.strip():
        with st.spinner("កំពុងគណនាម៉ោង និងបញ្ចូលសំឡេង..."):
            try:
                final_audio = asyncio.run(generate_audio(srt_input, voice_id, speed, pitch))
                if final_audio:
                    st.audio(final_audio, format="audio/mp3")
                    st.download_button("📥 ទាញយក MP3", final_audio, "khmer_strict_sync.mp3")
                    st.success("ផលិតជោគជ័យ! សំឡេងនីមួយៗចាប់ផ្តើមចំពេលដែលបានកំណត់។")
                else:
                    st.error("ទម្រង់ SRT មិនត្រឹមត្រូវ!")
            except Exception as e:
                st.error(f"បញ្ហា៖ {e}")
    else:
        st.warning("សូមបញ្ចូលអត្ថបទ SRT ជាមុនសិន!")

