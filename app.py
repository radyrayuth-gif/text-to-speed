import streamlit as st
import asyncio
import edge_tts
import re
from datetime import datetime

st.set_page_config(page_title="Khmer Perfect Sync 3.13", page_icon="🎙️")

def srt_time_to_ms(time_str):
    try:
        time_obj = datetime.strptime(time_str.strip().replace(',', '.'), '%H:%M:%S.%f')
        return (time_obj.hour * 3600000) + (time_obj.minute * 60000) + (time_obj.second * 1000) + (time_obj.microsecond // 1000)
    except:
        return 0

def parse_srt_clean(srt_text):
    # Regex នេះចាប់យកតែពេលវេលា និងអក្សរខ្មែរ (លុបលេខរៀងចេញ)
    blocks = re.split(r'\n\s*\n', srt_text.strip())
    subtitles = []
    for block in blocks:
        lines = block.strip().split('\n')
        time_line = next((l for l in lines if "-->" in l), None)
        # យកតែជួរដែលមិនមែនជាលេខរៀង និងមិនមែនជាពេលវេលា
        text_lines = [l.strip() for l in lines if "-->" not in l and not l.strip().isdigit()]
        
        if time_line and text_lines:
            start_ms = srt_time_to_ms(time_line.split("-->")[0])
            subtitles.append({"start": start_ms, "text": " ".join(text_lines)})
    return subtitles

async def generate_final_audio(subs, voice):
    # បង្កើត SSML ដែលបញ្ជាឱ្យ AI ឈប់រង់ចាំឱ្យចំវិនាទី
    ssml = f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='km-KH'>"
    current_ms = 0
    
    for sub in subs:
        wait_ms = sub["start"] - current_ms
        if wait_ms > 0:
            ssml += f"<break time='{wait_ms}ms'/>"
        
        # ផ្ញើតែអត្ថបទខ្មែរសុទ្ធ គ្មានម៉ោង គ្មានលេខរៀង
        ssml += f"{sub['text']}"
        
        # បន្ថែមការប៉ាន់ស្មានរយៈពេលអានខ្លីបំផុត ដើម្បីឱ្យឃ្លាបន្ទាប់ Sync ត្រូវ
        current_ms = sub["start"] + 200 
        
    ssml += "</speak>"
    
    communicate = edge_tts.Communicate(ssml, voice)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

st.title("🎙️ Khmer Sync TTS (Fixed for Python 3.13)")
st.info("កូដនេះមិនប្រើ pydub ទេ ដូច្នេះនឹងមិនមាន Error Module ទៀតឡើយ។")

voice_id = st.sidebar.selectbox("សំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
srt_input = st.text_area("បិទភ្ជាប់ SRT ទីនេះ:", height=300)

if st.button("🚀 ផលិតសំឡេង Sync"):
    if srt_input:
        subs = parse_srt_clean(srt_input)
        if subs:
            with st.spinner("កំពុងផលិត..."):
                try:
                    audio_bytes = asyncio.run(generate_final_audio(subs, voice_id))
                    st.audio(audio_bytes, format="audio/mp3")
                    st.download_button("📥 ទាញយក MP3", audio_bytes, "khmer_sync.mp3")
                except Exception as e:
                    st.error(f"កំហុស៖ {e}")
