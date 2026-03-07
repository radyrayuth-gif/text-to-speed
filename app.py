import streamlit as st
import asyncio
import edge_tts
import re
import io
from pydub import AudioSegment

# កំណត់ Configuration របស់ទំព័រ
st.set_page_config(page_title="Khmer TTS 100% Precision", page_icon="🎙️")

def parse_srt(srt_text):
    pattern = r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\n$|$)"
    matches = re.findall(pattern, srt_text, re.DOTALL)
    subtitles = []
    
    def to_ms(time_str):
        h, m, s = time_str.replace(',', '.').split(':')
        return int(int(h)*3600000 + int(m)*60000 + float(s)*1000)

    for match in matches:
        subtitles.append({
            "start_ms": to_ms(match[1]),
            "end_ms": to_ms(match[2]),
            "text": match[3].replace('\n', ' ').strip()
        })
    return subtitles

def adjust_speed(audio, target_ms):
    actual_ms = len(audio)
    if actual_ms <= target_ms or target_ms <= 0:
        return audio
    speed_factor = actual_ms / target_ms
    return audio.speedup(playback_speed=speed_factor, chunk_size=50, crossfade=25)

async def generate_audio(srt_text, voice, rate, pitch):
    subs = parse_srt(srt_text)
    if not subs: return None

    final_audio = AudioSegment.silent(duration=0, frame_rate=44100)
    
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"

    for sub in subs:
        communicate = edge_tts.Communicate(sub['text'], voice, rate=rate_str, pitch=pitch_str)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        seg = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3").set_frame_rate(44100)
        
        silence_needed = sub['start_ms'] - len(final_audio)
        if silence_needed > 0:
            final_audio += AudioSegment.silent(duration=silence_needed, frame_rate=44100)
        
        duration_limit = sub['end_ms'] - sub['start_ms']
        seg = adjust_speed(seg, duration_limit)
        
        final_audio = final_audio.overlay(seg, position=sub['start_ms'])

    buffer = io.BytesIO()
    final_audio.export(buffer, format="mp3")
    return buffer.getvalue()

# --- UI Layout ---
st.title("🎙️ Khmer TTS Precision (Final)")

col1, col2 = st.columns([2, 1])

with col2:
    st.write("⚙️ **ការកំណត់សំឡេង**")
    voice_option = st.selectbox("ជ្រើសរើសសំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
    rate_val = st.slider("ល្បឿននិយាយ (%)", min_value=-50, max_value=100, value=0, step=5)
    pitch_val = st.slider("កម្រិតសំឡេង (Pitch Hz)", min_value=-50, max_value=50, value=0, step=2)

with col1:
    srt_input = st.text_area("បញ្ចូល SRT របស់អ្នក:", height=300, value="""1
00:00:00,700 --> 00:00:02,340
ប្តីសម្លាញ់, ពួកយើងទៅ

2
00:00:03,500 --> 00:00:05,500
តើអ្នកត្រៀមខ្លួនហើយឬនៅ?""")

if st.button("🔊 ផលិតសំឡេង"):
    if srt_input:
        with st.spinner("កំពុងដំណើរការ..."):
            try:
                audio_bytes = asyncio.run(generate_audio(srt_input, voice_option, rate_val, pitch_val))
                st.audio(audio_bytes)
                st.download_button("📥 ទាញយក MP3", audio_bytes, "khmer_audio.mp3")
            except Exception as e:
                st.error(f"Error: {e}")
