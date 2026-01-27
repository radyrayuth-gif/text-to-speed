import streamlit as st
import asyncio
import edge_tts
import re
import base64
from datetime import datetime

st.set_page_config(page_title="Khmer TTS Master", page_icon="🎙️")

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

async def get_audio_data(text, voice, rate):
    rate_str = f"{rate:+d}%"
    communicate = edge_tts.Communicate(text, voice, rate=rate_str)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

st.title("🎙️ Khmer TTS Master (All-in-One Download)")

with st.sidebar:
    st.header("⚙️ ការកំណត់")
    voice_id = st.selectbox("ជ្រើសរើសសំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
    speed_rate = st.slider("ល្បឿនអាន (%)", -50, 50, 0, 5)

srt_input = st.text_area("បិទភ្ជាប់ SRT ទីនេះ:", height=300)

if st.button("🚀 ចាប់ផ្ដើមផលិត និងរួមបញ្ចូលសំឡេង"):
    if srt_input:
        subs = parse_srt_to_list(srt_input)
        if subs:
            all_audio_bytes = b"" # បង្កើត Variable សម្រាប់ទុកសំឡេងរួម
            
            # JavaScript សម្រាប់ចាក់អូតូតាមវិនាទី
            js_auto_play = "<script>function autoPlay(b64, time) { setTimeout(() => { var audio = new Audio('data:audio/mp3;base64,' + b64); audio.play(); }, time * 1000); }</script>"
            st.components.v1.html(js_auto_play, height=0)

            with st.spinner("កំពុងផលិត និងភ្ជាប់សំឡេងទាំងអស់ចូលគ្នា..."):
                for i, sub in enumerate(subs):
                    # ផលិតសំឡេងឃ្លានីមួយៗ
                    audio_bytes = asyncio.run(get_audio_data(sub["text"], voice_id, speed_rate))
                    all_audio_bytes += audio_bytes # បូកបញ្ចូលគ្នា
                    
                    audio_b64 = base64.b64encode(audio_bytes).decode()
                    
                    # បង្ហាញការ Preview និងចាក់អូតូ
                    with st.expander(f"ឃ្លាទី {i+1} (វិនាទីទី {sub['start']})"):
                        st.write(sub["text"])
                        st.audio(audio_bytes, format="audio/mp3")
                        st.components.v1.html(f"<script>window.parent.autoPlay('{audio_b64}', {sub['start']});</script>", height=0)
            
            # --- ប៊ូតុងទាញយកទាំងអស់ (រួមបញ្ចូលគ្នា) ---
            st.divider()
            st.subheader("📥 ទាញយកលទ្ធផលចុងក្រោយ")
            st.info("ប៊ូតុងខាងក្រោមនឹងទាញយកសំឡេងគ្រប់ឃ្លាទាំងអស់ដែលបានតភ្ជាប់គ្នាជា File តែមួយ។")
            st.download_button(
                label="📥 ទាញយកសំឡេងទាំងអស់ (Merge All MP3)",
                data=all_audio_bytes,
                file_name="khmer_full_audio.mp3",
                mime="audio/mp3",
                use_container_width=True
            )
            st.audio(all_audio_bytes, format="audio/mp3") # Player សម្រាប់ស្ដាប់សរុប
        else:
            st.error("ទម្រង់ SRT មិនត្រឹមត្រូវ!")
