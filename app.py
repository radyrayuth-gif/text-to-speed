import streamlit as st
import asyncio
import edge_tts
import re
import base64
from datetime import datetime

st.set_page_config(page_title="Khmer Sync & Download", page_icon="🎙️")

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

st.title("🎙️ Khmer TTS: Sync, Replay & Download")

with st.sidebar:
    st.header("⚙️ ការកំណត់")
    voice_id = st.selectbox("ជ្រើសរើសសំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
    speed_rate = st.slider("ល្បឿនអាន (%)", -50, 50, 0, 5)

srt_input = st.text_area("បិទភ្ជាប់ SRT ទីនេះ:", height=300)

if st.button("🚀 ចាប់ផ្ដើមផលិតសំឡេង"):
    if srt_input:
        subs = parse_srt_to_list(srt_input)
        if subs:
            st.success(f"ផលិតបាន {len(subs)} ឃ្លា។ សំឡេងនឹងចាក់អូតូតាមវិនាទីដែលអ្នកកំណត់។")
            
            # JavaScript សម្រាប់ចាក់អូតូតាមវិនាទី
            js_auto_play = """
            <script>
            function autoPlay(b64, time) {
                setTimeout(() => {
                    var audio = new Audio("data:audio/mp3;base64," + b64);
                    audio.play();
                }, time * 1000);
            }
            </script>
            """
            st.components.v1.html(js_auto_play, height=0)

            for i, sub in enumerate(subs):
                # ផលិតសំឡេង
                audio_bytes = asyncio.run(get_audio_data(sub["text"], voice_id, speed_rate))
                audio_b64 = base64.b64encode(audio_bytes).decode()
                
                # បង្កើតប្រអប់បង្ហាញឃ្លានីមួយៗ
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**⏱️ វិនាទីទី {sub['start']}**")
                        st.write(sub["text"])
                        # ចាក់អូតូតាមវិនាទី
                        st.components.v1.html(f"<script>window.parent.autoPlay('{audio_b64}', {sub['start']});</script>", height=0)
                    
                    with col2:
                        # ប៊ូតុងស្ដាប់ឡើងវិញ
                        st.audio(audio_bytes, format="audio/mp3")
                        # ប៊ូតុងទាញយក
                        st.download_button(
                            label="📥 Download",
                            data=audio_bytes,
                            file_name=f"part_{i+1}_{sub['start']}s.mp3",
                            mime="audio/mp3",
                            key=f"dl_{i}"
                        )
                    st.divider()
        else:
            st.error("ទម្រង់ SRT មិនត្រឹមត្រូវ!")
