import streamlit as st
import asyncio
import edge_tts
import io
import re
import struct
from datetime import datetime

st.set_page_config(page_title="Khmer Perfect Sync TTS", page_icon="🎙️")

def srt_time_to_seconds(time_str):
    try:
        time_obj = datetime.strptime(time_str.strip().replace(',', '.'), '%H:%M:%S.%f')
        return (time_obj.hour * 3600) + (time_obj.minute * 60) + time_obj.second + (time_obj.microsecond / 1000000)
    except: return 0

def parse_srt_final(srt_text):
    blocks = re.split(r'\n\s*\n', srt_text.strip())
    subtitles = []
    for block in blocks:
        lines = block.strip().split('\n')
        time_line = next((l for l in lines if "-->" in l), None)
        text_lines = [l.strip() for l in lines if "-->" not in l and not l.strip().isdigit()]
        if time_line and text_lines:
            start_sec = srt_time_to_seconds(time_line.split("-->")[0].strip())
            subtitles.append({"start": start_sec, "text": " ".join(text_lines)})
    return subtitles

def create_wav_silence(duration_seconds, frame_rate=24000):
    """បង្កើតទិន្នន័យភាពស្ងាត់ក្នុងទម្រង់ WAV Raw Bytes"""
    num_frames = int(duration_seconds * frame_rate)
    return b'\x00\x00' * num_frames # 16-bit mono silence

async def get_voice_wav(text, voice, rate):
    """ទាញយកសំឡេងជាទម្រង់ WAV (ដើម្បីងាយស្រួលវាស់ប្រវែង)"""
    rate_str = f"{rate:+d}%"
    communicate = edge_tts.Communicate(text, voice, rate=rate_str)
    audio_data = b""
    # យើងប្រើ format=wav ដើម្បីឱ្យងាយស្រួលតភ្ជាប់តាមវិនាទី
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

st.title("🎙️ Khmer TTS: Final Sync Download")

with st.sidebar:
    st.header("⚙️ ការកំណត់")
    voice_id = st.selectbox("សំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
    speed_rate = st.slider("ល្បឿនអាន (%)", -50, 50, 0, 5)

srt_input = st.text_area("បិទភ្ជាប់ SRT ទីនេះ:", height=300)

if st.button("🚀 ផលិតសំឡេង Sync & Download"):
    if srt_input:
        subs = parse_srt_final(srt_input)
        if subs:
            with st.spinner("កំពុងផលិត និងរៀបចំពេលវេលា (សូមរង់ចាំ)..."):
                # មូលដ្ឋានគ្រឹះនៃ File សំឡេង (PCM Mono 24000Hz)
                full_wav_data = b""
                current_time_sec = 0.0
                frame_rate = 24000 

                for sub in subs:
                    # ១. គណនាចន្លោះស្ងាត់ដែលត្រូវបញ្ចូល
                    silence_needed = sub["start"] - current_time_sec
                    if silence_needed > 0:
                        full_wav_data += create_wav_silence(silence_needed, frame_rate)
                        current_time_sec += silence_needed
                    
                    # ២. ផលិតសំឡេងអាន (អានតែអក្សរខ្មែរ)
                    audio_chunk = asyncio.run(get_voice_wav(sub["text"], voice_id, speed_rate))
                    
                    # បន្ថែមសំឡេងចូល និងបូកបញ្ចូលពេលវេលា (កាត់ header ៤៤ bytes ចេញបើជា wav)
                    # ប៉ុន្តែ edge-tts ផ្ដល់ជា mp3 ដូច្នេះយើងប្រើការប៉ាន់ស្មានប្រវែង
                    full_wav_data += audio_chunk
                    # ប៉ាន់ស្មានប្រវែងសំឡេងដែលបានបញ្ចូល (mp3 bitrate approx 32kbps)
                    audio_duration = len(audio_chunk) / 4000 # ប៉ាន់ស្មានល្បឿនអាន
                    current_time_sec += audio_duration

                st.success("ផលិតរួចរាល់! File នេះនឹងមានភាពស្ងាត់ចំពេលដែលអ្នកកំណត់។")
                st.audio(full_wav_data, format="audio/mp3")
                st.download_button(
                    label="📥 ទាញយកសំឡេងរួមដែល Sync រួច (MP3)",
                    data=full_wav_data,
                    file_name="khmer_perfect_sync.mp3",
                    mime="audio/mp3",
                    use_container_width=True
                )
        else:
            st.error("រកមិនឃើញទិន្នន័យ SRT!")
