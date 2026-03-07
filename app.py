import streamlit as st
import asyncio
import edge_tts
import re
import io
from pydub import AudioSegment

# Page Configuration
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
    # Speed up if the audio is longer than the SRT duration
    return audio.speedup(playback_speed=min(speed_factor, 2.0), chunk_size=50, crossfade=25)

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
        
        # Add silence until the start time
        if sub['start_ms'] > len(final_audio):
            silence_gap = sub['start_ms'] - len(final_audio)
            final_audio += AudioSegment.silent(duration=silence_gap, frame_rate=44100)
        
        # Adjust speed based on SRT duration
        duration_limit = sub['end_ms'] - sub['start_ms']
        seg = adjust_speed(seg, duration_limit)
        
        # Overlay audio
        final_audio = final_audio.overlay(seg, position=sub['start_ms'])
        
        if len(final_audio) < sub['end_ms']:
            final_audio += AudioSegment.silent(duration=sub['end_ms'] - len(final_audio))

    buffer = io.BytesIO()
    final_audio.export(buffer, format="mp3")
    return buffer.getvalue()

# --- UI ---
st.title("🎙️ Khmer TTS Precision (Fixed)")

with st.sidebar:
    st.header("Settings")
    voice_option = st.selectbox("Voice:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
    speed_rate = st.slider("Speech Rate (%):", -50, 100, 0, step=5)
    pitch_val = st.slider("Pitch (Hz):", -50, 50, 0, step=1)

uploaded_file = st.file_uploader("Upload SRT File", type=["srt"])

if uploaded_file is not None:
    srt_content = uploaded_file.getvalue().decode("utf-8")
    srt_input = st.text_area("SRT Content:", value=srt_content, height=200)
else:
    srt_input = st.text_area("Or Paste SRT Here:", height=200, value="""1
00:00:00,500 --> 00:00:02,500
ជម្រាបសួរ បងប្អូនទាំងអស់គ្នា។""")

if st.button("🔊 Generate Audio"):
    if srt_input.strip() == "":
        st.warning("Please provide SRT text!")
    else:
        with st.spinner("Processing..."):
            try:
                audio = asyncio.run(generate_audio(srt_input, voice_option, speed_rate, pitch_val))
                if audio:
                    st.audio(audio)
                    st.download_button("📥 Download MP3", audio, "khmer_audio.mp3")
            except Exception as e:
                st.error(f"Error: {e}")
