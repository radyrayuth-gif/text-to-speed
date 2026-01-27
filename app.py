import streamlit as st
import asyncio
import edge_tts
import re
import base64
from datetime import datetime

st.set_page_config(page_title="Khmer Perfect Sync", page_icon="🎙️")

def srt_time_to_seconds(time_str):
    """បំប្លែងពេលវេលាពី SRT ទៅជាវិនាទីសុទ្ធ"""
    try:
        time_obj = datetime.strptime(time_str.strip().replace(',', '.'), '%H:%M:%S.%f')
        return (time_obj.hour * 3600) + (time_obj.minute * 60) + time_obj.second + (time_obj.microsecond / 1000000)
    except:
        return 0

def parse_srt_to_list(srt_text):
    """ច្រោះយកតែអត្ថបទខ្មែរ និងវិនាទីចាប់ផ្ដើម (លុបលេខរៀង និងម៉ោងចេញពីការអាន)"""
    blocks = re.split(r'\n\s*\n', srt_text.strip())
    subtitles = []
    for block in blocks:
        lines = block.strip().split('\n')
        time_line = next((l for l in lines if "-->" in l), None)
        # យកតែជួរអត្ថបទខ្មែរ មិនយកជួរលេខរៀង និងជួរម៉ោង
        text_lines = [l.strip() for l in lines if "-->" not in l and not l.strip().isdigit()]
        
        if time_line and text_lines:
            start_sec = srt_time_to_seconds(time_line.split("-->")[0].strip())
            subtitles.append({
                "start": start_sec,
                "text": " ".join(text_lines)
            })
    return subtitles

async def get_audio_base64(text, voice):
    """ផលិតសំឡេងជា Base64 ដើម្បីចាក់ក្នុង Browser"""
    communicate = edge_tts.Communicate(text, voice)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return base64.b64encode(audio_data).decode()

st.title("🎙️ Khmer TTS: Perfect Timing Sync")
st.write("សំឡេងនឹងអានចំវិនាទីដែលកំណត់ក្នុង SRT ទោះបីឃ្លានីមួយៗនៅឆ្ងាយពីគ្នាក៏ដោយ។")

voice_id = st.sidebar.selectbox("ជ្រើសរើសសំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
srt_input = st.text_area("បិទភ្ជាប់អត្ថបទ SRT ទីនេះ:", height=300)

if st.button("🚀 ផលិតសំឡេង Sync"):
    if srt_input:
        subs = parse_srt_to_list(srt_input)
        if subs:
            with st.spinner("កំពុងផលិតសំឡេងតាមវិនាទី..."):
                # រៀបចំកូដ JavaScript ដើម្បីចាក់សំឡេងតាមវិនាទី
                js_code = """
                <script>
                function playAudioAtTime(base64Data, startTime) {
                    setTimeout(() => {
                        var audio = new Audio("data:audio/mp3;base64," + base64Data);
                        audio.play();
                    }, startTime * 1000);
                }
                </script>
                """
                
                # បង្កើត Audio Players សម្រាប់ឃ្លានីមួយៗ
                for sub in subs:
                    audio_b64 = asyncio.run(get_audio_base64(sub["text"], voice_id))
                    st.components.v1.html(f"""
                        {js_code}
                        <div style="padding:10px; border-bottom:1px solid #eee;">
                            <b>វិនាទីទី {sub['start']}:</b> {sub['text']}
                            <script>playAudioAtTime("{audio_b64}", {sub['start']});</script>
                        </div>
                    """, height=60)
                
                st.success("ផលិតរួចរាល់! សំឡេងនឹងចាប់ផ្ដើមអានដោយស្វ័យប្រវត្តិតាមវិនាទីនីមួយៗ។")
        else:
            st.error("ទម្រង់ SRT មិនត្រឹមត្រូវ!")
