import streamlit as st
import asyncio
import edge_tts
import re
import io
from pydub import AudioSegment

# --- កំណត់ទំព័រ ---
st.set_page_config(page_title="Khmer TTS Pro", page_icon="🎙️")

def parse_srt(srt_text):
    pattern = r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\n$|$)"
    matches = re.findall(pattern, srt_text, re.DOTALL)
    subtitles = []
    def to_ms(time_str):
        h, m, s = time_str.replace(',', '.').split(':')
        return int(h)*3600000 + int(m)*60000 + float(s)*1000
    for m in matches:
        subtitles.append({"start_ms": to_ms(m[1]), "end_ms": to_ms(m[2]), "text": m[3].strip()})
    return subtitles

async def generate_audio(srt_text, voice, rate, pitch):
    subs = parse_srt(srt_text)
    combined_audio = AudioSegment.empty()
    current_ms = 0
    
    for sub in subs:
        # ថែមចន្លោះស្ងាត់មុនអាន
        silence_duration = sub['start_ms'] - current_ms
        if silence_duration > 0:
            combined_audio += AudioSegment.silent(duration=silence_duration)
        
        # បង្កើតសំឡេង
        comm = edge_tts.Communicate(sub['text'], voice, rate=f"{rate:+d}%", pitch=f"{pitch:+d}Hz")
        audio_data = b""
        async for chunk in comm.stream():
            if chunk["type"] == "audio": audio_data += chunk["data"]
        
        segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
        
        # សារ៉េល្បឿនឱ្យត្រូវតាមម៉ោង SRT
        target_dur = sub['end_ms'] - sub['start_ms']
        if len(segment) > target_dur and target_dur > 0:
            segment = segment.speedup(playback_speed=len(segment)/target_dur)
        
        combined_audio += segment
        current_ms = len(combined_audio)

    buffer = io.BytesIO()
    combined_audio.export(buffer, format="mp3")
    return buffer.getvalue()

st.title("🎙️ Khmer SRT Audio Dubbing")

# UI Settings
voice_choice = st.selectbox("ជ្រើសរើសអ្នកអាន:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
speed = st.slider("ល្បឿន (%):", -50, 50, 0)
pitch = st.slider("កម្រិតសំឡេង (Hz):", -20, 20, 0)
srt_input = st.text_area("បញ្ចូល SRT:", height=200)

if st.button("🔊 ចាប់ផ្តើមផលិត"):
    try:
        audio = asyncio.run(generate_audio(srt_input, voice_choice, speed, pitch))
        st.audio(audio)
    except Exception as e:
        st.error(f"បញ្ហា៖ {e}")
        st.info("ប្រសិនបើឃើញ Error 'ffprobe' មានន័យថា packages.txt មិនទាន់ដំណើរការ។ សូមលុប App រួច Deploy ឡើងវិញ។")
