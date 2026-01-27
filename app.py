import streamlit as st
import asyncio
import edge_tts
import re
from datetime import datetime

st.set_page_config(page_title="Khmer Perfect Sync", page_icon="🎙️")

def srt_time_to_ms(time_str):
    """បំប្លែងពេលវេលាពី SRT ទៅជា Milliseconds"""
    try:
        time_obj = datetime.strptime(time_str.strip().replace(',', '.'), '%H:%M:%S.%f')
        return (time_obj.hour * 3600000) + (time_obj.minute * 60000) + (time_obj.second * 1000) + (time_obj.microsecond // 1000)
    except:
        return 0

def parse_srt_sync(srt_text):
    """ទាញយកពេលវេលា និងអត្ថបទ ដោយលុបលេខរៀង និងម៉ោងនាទីចេញពីការអាន"""
    blocks = re.split(r'\n\s*\n', srt_text.strip())
    subtitles = []
    for block in blocks:
        lines = block.strip().split('\n')
        time_line = next((l for l in lines if "-->" in l), None)
        # យកតែជួរអត្ថបទខ្មែរ (មិនយកជួរម៉ោង និងជួរលេខរៀង)
        text_lines = [l.strip() for l in lines if "-->" not in l and not l.strip().isdigit()]
        
        if time_line and text_lines:
            start_ms = srt_time_to_ms(time_line.split("-->")[0])
            subtitles.append({"start": start_ms, "text": " ".join(text_lines)})
    return subtitles

async def generate_synced_audio(subs, voice):
    """ប្រើ SSML បញ្ជាឱ្យ AI ផ្អាក (Break) តាមវិនាទីជាក់លាក់ក្នុង SRT"""
    # ចាប់ផ្ដើម SSML
    ssml = f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='km-KH'>"
    
    current_ms = 0
    for sub in subs:
        # គណនាចន្លោះដែលត្រូវផ្អាក (ឧទាហរណ៍៖ ពីវិនាទីទី ០ ទៅ វិនាទីទី ៥៤)
        wait_time = sub["start"] - current_ms
        if wait_time > 0:
            ssml += f"<break time='{wait_time}ms'/>"
        
        # បន្ថែមអត្ថបទខ្មែរសុទ្ធ (AI នឹងមិនឃើញលេខរៀង ឬម៉ោងឡើយ)
        ssml += sub["text"]
        
        # ចំណាំ៖ យើងត្រូវបូកបន្ថែមរយៈពេលអានខ្លីបំផុត ដើម្បីឱ្យការគណនាឃ្លាបន្ទាប់មិនជាន់គ្នា
        # ក្នុងករណីនេះ យើងសន្មតថាការអានប្រើពេល ១០០ms ជាមូលដ្ឋាន
        current_ms = sub["start"] + 100 

    ssml += "</speak>"
    
    communicate = edge_tts.Communicate(ssml, voice)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

st.title("🎙️ Khmer TTS: Sync តាមវិនាទី SRT")
st.write("សំឡេងនឹងអានចំពេលដែលអ្នកកំណត់ក្នុង SRT (ឧទាហរណ៍៖ វិនាទីទី ៥៤ គឺអាននៅវិនាទីទី ៥៤)។")

voice_id = st.sidebar.selectbox("សំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
srt_input = st.text_area("បិទភ្ជាប់ SRT ទីនេះ:", height=300)

if st.button("🚀 ផលិតសំឡេង Sync"):
    if srt_input:
        subs = parse_srt_sync(srt_input)
        if subs:
            with st.spinner("កំពុងគណនាចន្លោះផ្អាក និងផលិតសំឡេង..."):
                try:
                    audio_bytes = asyncio.run(generate_synced_audio(subs, voice_id))
                    st.success("ផលិតជោគជ័យ!")
                    st.audio(audio_bytes, format="audio/mp3")
                    st.download_button("📥 ទាញយក MP3", audio_bytes, "khmer_sync_final.mp3")
                except Exception as e:
                    st.error(f"កំហុស៖ {e}")
