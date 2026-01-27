import streamlit as st
import asyncio
import edge_tts
import re
import io
import base64
from datetime import datetime
from pydub import AudioSegment

st.set_page_config(page_title="Khmer Perfect Sync", page_icon="🎙️")

def srt_time_to_seconds(time_str):
    try:
        time_obj = datetime.strptime(time_str.strip().replace(',', '.'), '%H:%M:%S.%f')
        return (time_obj.hour * 3600) + (time_obj.minute * 60) + time_obj.second + (time_obj.microsecond / 1000000)
    except:
        return 0

def parse_srt_to_list(srt_text):
    blocks = re.split(r'\n\s*\n', srt_text.strip())
    subtitles = []
    for block in blocks:
        lines = block.strip().split('\n')
        time_line = next((l for l in lines if "-->" in l), None)
        text_lines = [l.strip() for l in lines if "-->" not in l and not l.strip().isdigit()]
        
        if time_line and text_lines:
            start_sec = srt_time_to_seconds(time_line.split("-->")[0].strip())
            subtitles.append({
                "start": start_sec,
                "text": " ".join(text_lines)
            })
    return subtitles

async def generate_audio_segment(text, voice, rate):
    """ផលិតសំឡេងជា AudioSegment របស់ pydub"""
    # កំណត់ល្បឿន (ឧទាហរណ៍: +10% ឬ -10%)
    rate_str = f"{rate:+d}%"
    communicate = edge_tts.Communicate(text, voice, rate=rate_str)
    
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    
    return AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")

st.title("🎙️ Khmer TTS: Sync & Download")
st.write("ផលិតសំឡេងខ្មែរតាមវិនាទី SRT និងអាចទាញយកជា File តែមួយបាន។")

# Sidebar settings
st.sidebar.header("ការកំណត់")
voice_id = st.sidebar.selectbox("ជ្រើសរើសសំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
speed = st.sidebar.slider("ល្បឿននិយាយ (%)", min_value=-50, max_value=50, value=0, step=5)
srt_input = st.text_area("បិទភ្ជាប់អត្ថបទ SRT ទីនេះ:", height=250)

if st.button("🚀 ផលិត និងទាញយកសំឡេង"):
    if srt_input:
        subs = parse_srt_to_list(srt_input)
        if subs:
            with st.spinner("កំពុងដំណើរការផលិតសំឡេង និងរៀបចំ Timeline..."):
                final_audio = AudioSegment.silent(duration=0) # ចាប់ផ្ដើមពីទទេ
                
                for sub in subs:
                    # ផលិតសំឡេងសម្រាប់ឃ្លានីមួយៗ
                    segment = asyncio.run(generate_audio_segment(sub["text"], voice_id, speed))
                    
                    # គណនាទីតាំងដែលត្រូវដាក់ក្នុង Timeline
                    start_ms = int(sub["start"] * 1000)
                    
                    # បន្ថែម Silence បើវិនាទីចាប់ផ្ដើមលើសពីប្រវែងសំឡេងបច្ចុប្បន្ន
                    if len(final_audio) < start_ms:
                        silence_duration = start_ms - len(final_audio)
                        final_audio += AudioSegment.silent(duration=silence_duration)
                    
                    # បញ្ចូលសំឡេងទៅក្នុង Timeline
                    final_audio = final_audio.overlay(segment, position=start_ms)

                # រក្សាទុកក្នុង Memory ដើម្បី Download
                buffer = io.BytesIO()
                final_audio.export(buffer, format="mp3")
                
                # បង្ហាញ Player និងប៊ូតុង Download
                st.audio(buffer.getvalue(), format="audio/mp3")
                st.download_button(
                    label="📥 ទាញយកឯកសារសំឡេង (.mp3)",
                    data=buffer.getvalue(),
                    file_name=f"khmer_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3",
                    mime="audio/mp3"
                )
                st.success("ការផលិតបានជោគជ័យ!")
        else:
            st.error("ទម្រង់ SRT មិនត្រឹមត្រូវ!")
