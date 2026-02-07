import streamlit as st
import asyncio
import edge_tts
import re
import io
from pydub import AudioSegment

# --- កំណត់ទំព័រ ---
st.set_page_config(page_title="Khmer TTS Precision Sync", page_icon="🎙️")

def parse_srt(srt_text):
    # ចាប់យកលេខរៀង ម៉ោងចាប់ផ្តើម និងអត្ថបទ
    pattern = r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\n$|$)"
    matches = re.findall(pattern, srt_text, re.DOTALL)
    subtitles = []
    
    def to_ms(time_str):
        h, m, s = time_str.replace(',', '.').split(':')
        return int(h)*3600000 + int(m)*60000 + float(s)*1000

    for match in matches:
        subtitles.append({
            "start_ms": int(to_ms(match[1])),
            "text": match[3].strip()
        })
    return subtitles

async def generate_audio(srt_text, voice, rate, pitch):
    subs = parse_srt(srt_text)
    if not subs: return None

    # ១. បង្កើត Timeline ស្ងាត់មួយដែលមានរយៈពេលវែងជាមុន (ឧទាហរណ៍ ២ ម៉ោង) 
    # ដើម្បីធានាថាគ្រប់ Start Time ទាំងអស់មានកន្លែងអង្គុយត្រឹមត្រូវ
    max_time = subs[-1]['start_ms'] + 20000 # បន្ថែម ២០ វិនាទីការពារដាច់កន្ទុយ
    final_audio = AudioSegment.silent(duration=max_time)
    
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"

    for i, sub in enumerate(subs):
        # ២. ផលិតសំឡេង AI សម្រាប់ឃ្លានីមួយៗ
        communicate = edge_tts.Communicate(sub['text'], voice, rate=rate_str, pitch=pitch_str)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
        
        # ៣. ការពារការជាន់គ្នាដោយពន្លឿនល្បឿន (Smart Speedup)
        # ពិនិត្យថា តើឃ្លានេះអានវែងជាងចន្លោះពេលទៅឃ្លាបន្ទាប់ឬទេ?
        if i < len(subs) - 1:
            available_ms = subs[i+1]['start_ms'] - sub['start_ms']
            actual_ms = len(segment)
            
            if actual_ms > available_ms and available_ms > 0:
                # ពន្លឿនសំឡេងឱ្យខ្លីល្មមនឹងចន្លោះពេលដែលមាន
                speed_ratio = actual_ms / available_ms
                segment = segment.speedup(playback_speed=speed_ratio)
        
        # ៤. ដាក់បញ្ចូលទៅក្នុង Timeline ចំ Start Time ដែលកំណត់ក្នុង SRT
        # យើងប្រើ position=sub['start_ms'] ដើម្បីបង្ខំឱ្យវាចាប់ផ្តើមចំវិនាទីនោះ
        final_audio = final_audio.overlay(segment, position=sub['start_ms'])

    # កាត់ផ្នែកស្ងាត់ដែលនៅសល់កន្ទុយចេញ
    final_audio = final_audio.strip_silence(silence_thresh=-50, padding=100)

    buffer = io.BytesIO()
    final_audio.export(buffer, format="mp3")
    return buffer.getvalue()

# --- ចំណុចប្រទាក់អ្នកប្រើ (UI) ---
st.title("🎙️ Khmer TTS Precision Sync")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    voice = st.selectbox("ជ្រើសរើសសំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
    speed = st.slider("ល្បឿនមូលដ្ឋាន:", -50, 50, 0)
with col2:
    pitch = st.slider("កម្រិតសំឡេង:", -20, 20, 0)
    
srt_input = st.text_area("បញ្ចូល SRT របស់អ្នក (សូមពិនិត្យមើលទ្រង់ទ្រាយឱ្យបានត្រឹមត្រូវ):", height=300, 
                         placeholder="1\n00:00:01,500 --> 00:00:03,000\nសួស្តីបងប្អូន...")

if st.button("🔊 ចាប់ផ្តើមផលិតសំឡេង"):
    if srt_input:
        with st.spinner("កំពុងរៀបចំសំឡេងឱ្យត្រូវចំវិនាទី..."):
            try:
                result = asyncio.run(generate_audio(srt_input, voice, speed, pitch))
                if result:
                    st.audio(result)
                    st.download_button("📥 ទាញយក MP3", result, "precision_sync.mp3")
                    st.success("ផលិតរួចរាល់! សំឡេងនឹងចាប់ផ្តើមត្រូវចំម៉ោង Start Time ជានិច្ច។")
            except Exception as e:
                st.error(f"មានបញ្ហាបច្ចេកទេស៖ {e}")
    else:
        st.warning("សូមបញ្ចូល SRT ជាមុន!")
