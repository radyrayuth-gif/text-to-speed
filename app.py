import streamlit as st
import asyncio
import edge_tts
import re
import base64
from datetime import datetime

st.set_page_config(page_title="Khmer Perfect Sync for Video", page_icon="🎙️")

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
            subtitles.append({"start": start_sec, "text": " ".join(text_lines)})
    return subtitles

async def generate_combined_audio(subs, voice, rate):
    # បង្កើត SSML ដើម្បីឱ្យ AI អាន និងផ្អាកតាមវិនាទីក្នុង File តែមួយ
    rate_str = f"{rate:+d}%"
    ssml = f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='km-KH'>"
    
    current_time = 0.0
    for sub in subs:
        # គណនាចន្លោះស្ងាត់ (Break) រវាងឃ្លា
        wait_time = sub["start"] - current_time
        if wait_time > 0:
            # បញ្ចូលចន្លោះស្ងាត់ (គិតជា Milliseconds)
            ssml += f"<break time='{int(wait_time * 1000)}ms'/>"
        
        ssml += f"<prosody rate='{rate_str}'>{sub['text']}</prosody>"
        
        # បូកបន្ថែមរយៈពេលប៉ាន់ស្មានដែល AI អាន (ដើម្បីកុំឱ្យឃ្លាបន្ទាប់រុញគ្នា)
        # យើងសន្មតថាការអានប្រើពេលខ្លីបំផុត 0.5 វិនាទី
        current_time = sub["start"] + 0.5
        
    ssml += "</speak>"
    
    communicate = edge_tts.Communicate(ssml, voice)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

st.title("🎙️ Khmer TTS Master (សម្រាប់ដាក់ក្នុងវីដេអូ)")

with st.sidebar:
    st.header("⚙️ ការកំណត់")
    voice_id = st.selectbox("ជ្រើសរើសសំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
    speed_rate = st.slider("ល្បឿនអាន (%)", -50, 50, 0, 5)

srt_input = st.text_area("បិទភ្ជាប់ SRT ទីនេះ:", height=300)

if st.button("🚀 ផលិតសំឡេងសម្រាប់ដោនឡូត"):
    if srt_input:
        subs = parse_srt_to_list(srt_input)
        if subs:
            with st.spinner("កំពុងផលិត File សំឡេងរួមដែលមានចន្លោះស្ងាត់..."):
                try:
                    # ផលិតសំឡេងរួមដែលមានការ Sync រួចជាស្រេច
                    final_audio = asyncio.run(generate_combined_audio(subs, voice_id, speed_rate))
                    
                    st.success("ផលិតរួចរាល់! អ្នកអាចស្ដាប់ និងទាញយក File រួមខាងក្រោម។")
                    
                    # Player សម្រាប់ស្ដាប់សរុប
                    st.audio(final_audio, format="audio/mp3")
                    
                    # ប៊ូតុងទាញយក File តែមួយគត់សម្រាប់ដាក់ក្នុងវីដេអូ
                    st.download_button(
                        label="📥 ទាញយកសំឡេងរួមទាំងអស់ (MP3)",
                        data=final_audio,
                        file_name="khmer_video_voice.mp3",
                        mime="audio/mp3",
                        use_container_width=True
                    )
                    
                    st.info("បញ្ជាក់៖ File នេះមានបញ្ចូលចន្លោះស្ងាត់តាមនាទី SRT រួចហើយ។")
                    
                except Exception as e:
                    st.error(f"កំហុស៖ {e}")
        else:
            st.error("ទម្រង់ SRT មិនត្រឹមត្រូវ!")
