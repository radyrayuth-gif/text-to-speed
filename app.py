import streamlit as st
import asyncio
import edge_tts
import re
import base64
from datetime import datetime

st.set_page_config(page_title="Khmer Sync TTS", page_icon="🎙️")

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

async def get_audio_base64(text, voice, rate):
    # កំណត់ល្បឿនអាន (ឧទាហរណ៍៖ +10% ឬ -10%)
    rate_str = f"{rate:+d}%"
    communicate = edge_tts.Communicate(text, voice, rate=rate_str)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return base64.b64encode(audio_data).decode()

st.title("🎙️ Khmer TTS: Sync & Speed Control")

with st.sidebar:
    st.header("⚙️ ការកំណត់សំឡេង")
    voice_id = st.selectbox("ជ្រើសរើសសំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
    # បន្ថែមរបារសារ៉េល្បឿន
    speed_rate = st.slider("ល្បឿនអាន (%)", -50, 50, 0, 5)

srt_input = st.text_area("បិទភ្ជាប់អត្ថបទ SRT ទីនេះ:", height=300)

if st.button("🚀 ចាប់ផ្ដើមផលិតសំឡេង Sync"):
    if srt_input:
        subs = parse_srt_to_list(srt_input)
        if subs:
            with st.spinner("កំពុងរៀបចំសំឡេង..."):
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
                for sub in subs:
                    # បញ្ជូនល្បឿនដែលបានសារ៉េទៅកាន់មុខងារផលិតសំឡេង
                    audio_b64 = asyncio.run(get_audio_base64(sub["text"], voice_id, speed_rate))
                    st.components.v1.html(f"""
                        {js_code}
                        <div style="padding:10px; border-bottom:1px solid #eee; font-family: 'Kantumruy Pro', sans-serif;">
                            <span style="color: #ff4b4b;">⏱️ {sub['start']}ស៖</span> {sub['text']}
                            <script>playAudioAtTime("{audio_b64}", {sub['start']});</script>
                        </div>
                    """, height=60)
                st.success(f"រួចរាល់! កំពុងអានក្នុងល្បឿន {speed_rate}%")
        else:
            st.error("ទម្រង់ SRT មិនត្រឹមត្រូវ!")
