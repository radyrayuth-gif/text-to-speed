import streamlit as st
import asyncio
import edge_tts
import re
import io
from pydub import AudioSegment

# --- កំណត់ទំព័រ ---
st.set_page_config(page_title="Khmer TTS Pro - លោកពូប៉ាវ", page_icon="🎙️")

def parse_srt(srt_text):
    pattern = r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\n$|$)"
    matches = re.findall(pattern, srt_text, re.DOTALL)
    subtitles = []
    def to_ms(time_str):
        h, m, s = time_str.replace(',', '.').split(':')
        return int(h)*3600000 + int(m)*60000 + float(s)*1000
    for match in matches:
        subtitles.append({
            "start_ms": to_ms(match[1]),
            "text": match[3].strip()
        })
    return subtitles

async def generate_audio(srt_text, voice, rate, pitch):
    subs = parse_srt(srt_text)
    
    # ១. រកមើលម៉ោងបញ្ចប់ចុងក្រោយបង្អស់ ដើម្បីបង្កើត Timeline ឱ្យវែងល្មម
    # យើងបន្ថែម ៥ វិនាទីទៀត ដើម្បីកុំឱ្យដាច់សំឡេងចុងក្រោយ
    max_duration = subs[-1]['start_ms'] + 5000 if subs else 0
    final_combined = AudioSegment.silent(duration=max_duration)
    
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"

    for sub in subs:
        # ២. បង្កើតសំឡេង AI
        communicate = edge_tts.Communicate(sub['text'], voice, rate=rate_str, pitch=pitch_str)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
        
        # ៣. ប្រើ position parameter នៅក្នុង overlay ដើម្បីបង្ខំឱ្យវាដាក់ចំ Start Time
        # វិធីនេះនឹងធ្វើឱ្យវាលោតទៅអានចំវិនាទីដែលអ្នកកំណត់ជានិច្ច
        final_combined = final_combined.overlay(segment, position=sub['start_ms'])

    # កាត់ផ្នែកដែលនៅសល់ (Silence) ចោលវិញក្រោយពេលបញ្ចូលរួច
    # (Optional: បើចង់ឱ្យ File តូច អាចកាត់ត្រឹមចុងបញ្ចប់នៃសំឡេងចុងក្រោយ)

    buffer = io.BytesIO()
    final_combined.export(buffer, format="mp3")
    return buffer.getvalue()

# --- UI (រក្សាដូចដើម) ---
st.title("🎙️ Khmer SRT (Strict Start Time Fix)")
st.write("ជំនាន់កែសម្រួល៖ បង្ខំឱ្យអានចំម៉ោង Start Time គ្រប់បន្ទាត់")

voice_choice = st.selectbox("ជ្រើសរើសអ្នកអាន:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
speed = st.slider("ល្បឿន (%):", -50, 50, 0, 5)
pitch = st.slider("កម្រិតសំឡេង (Hz):", -20, 20, 0, 1)
srt_input = st.text_area("បញ្ចូល SRT:", height=250)

if st.button("🔊 ផលិតសំឡេង"):
    if srt_input.strip():
        with st.spinner("កំពុងដាក់សំឡេងចូល Timeline..."):
            try:
                final_audio = asyncio.run(generate_audio(srt_input, voice_choice, speed, pitch))
                st.audio(final_audio)
                st.download_button("📥 ទាញយក MP3", final_audio, "strict_sync.mp3")
            except Exception as e:
                st.error(f"បញ្ហា៖ {e}")
