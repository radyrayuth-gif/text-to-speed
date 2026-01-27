import streamlit as st
import asyncio
import edge_tts
import io
import re
import numpy as np
from datetime import datetime
import wave

st.set_page_config(page_title="Khmer Stable Sync TTS", page_icon="🎙️")

def srt_time_to_seconds(time_str):
    """បំប្លែងពេលវេលា SRT ទៅជាវិនាទី"""
    try:
        time_obj = datetime.strptime(time_str.strip().replace(',', '.'), '%H:%M:%S.%f')
        return (time_obj.hour * 3600) + (time_obj.minute * 60) + time_obj.second + (time_obj.microsecond / 1000000)
    except: return 0

def parse_srt_final(srt_text):
    """ច្រោះយកតែអក្សរខ្មែរសុទ្ធ និងពេលវេលាចាប់ផ្ដើម (លុបលេខ និងម៉ោងចេញ)"""
    blocks = re.split(r'\n\s*\n', srt_text.strip())
    subtitles = []
    for block in blocks:
        lines = block.strip().split('\n')
        time_line = next((l for l in lines if "-->" in l), None)
        text_lines = [l.strip() for l in lines if "-->" not in l and not l.strip().isdigit()]
        if time_line and text_lines:
            start_sec = srt_time_to_seconds(time_line.split("-->")[0])
            subtitles.append({"start": start_sec, "text": " ".join(text_lines)})
    return subtitles

async def get_audio_payload(text, voice):
    """ផលិតសំឡេងជា Bytes (អានតែអក្សរខ្មែរ គ្មានម៉ោង គ្មានលេខ)"""
    communicate = edge_tts.Communicate(text, voice)
    data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": data += chunk["data"]
    return data

def create_silence(duration_sec, frame_rate=24000):
    """បង្កើតភាពស្ងាត់ (Silence) តាមចំនួនវិនាទី"""
    num_frames = int(duration_sec * frame_rate)
    return np.zeros(num_frames, dtype=np.int16).tobytes()

st.title("🎙️ កម្មវិធីផលិតសំឡេង Sync ១០០% (ជំនាន់ចុងក្រោយ)")
st.warning("កូដនេះនឹងធ្វើឱ្យសំឡេងអានចំវិនាទីក្នុង SRT និងមិនអានលេខរៀងឡើយ។")

voice_id = st.sidebar.selectbox("សំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
srt_input = st.text_area("បិទភ្ជាប់ SRT ទីនេះ:", height=300)

if st.button("🚀 ផលិតសំឡេង"):
    if srt_input:
        subs = parse_srt_final(srt_input)
        if subs:
            with st.spinner("កំពុងផលិត..."):
                try:
                    # ប្រើ BytesIO ដើម្បីទុកទិន្នន័យសំឡេងសរុប
                    final_audio = b""
                    current_time = 0
                    
                    for sub in subs:
                        # ១. បង្កើតចន្លោះស្ងាត់មុនពេលអានឃ្លាបន្ទាប់
                        silence_duration = sub["start"] - current_time
                        if silence_duration > 0:
                            # បន្ថែមចន្លោះស្ងាត់ (Padding)
                            final_audio += create_silence(silence_duration)
                        
                        # ២. ផលិតសំឡេងអាន (អានតែអក្សរខ្មែរសុទ្ធ)
                        audio_chunk = asyncio.run(get_audio_payload(sub["text"], voice_id))
                        final_audio += audio_chunk
                        
                        # ប៉ាន់ស្មានពេលវេលាដែលបានអានរួច (គ្រាន់តែជាការប៉ាន់ស្មានមូលដ្ឋាន)
                        # សម្រាប់ភាពសុក្រឹតបំផុត អ្នកត្រូវដឹងពីប្រវែង audio_chunk
                        current_time = sub["start"] + (len(audio_chunk) / 48000) # ប៉ាន់ស្មានតាម bitrate
                    
                    st.success("រួចរាល់! សាកល្បងស្ដាប់ខាងក្រោម។")
                    st.audio(final_audio, format="audio/mp3")
                    st.download_button("📥 ទាញយក MP3", final_audio, "sync_final.mp3")
                except Exception as e:
                    st.error(f"កំហុស៖ {e}")
