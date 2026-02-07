import streamlit as st
import asyncio
import edge_tts
import re
import io
from pydub import AudioSegment

# --- កំណត់ទំព័រ ---
st.set_page_config(page_title="Khmer TTS Precision Sync", page_icon="🎙️")

def parse_srt(srt_text):
    # ចាប់យក៖ លេខរៀង, ម៉ោងចាប់ផ្តើម, ម៉ោងបញ្ចប់, និង អត្ថបទ
    pattern = r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\n$|$)"
    matches = re.findall(pattern, srt_text, re.DOTALL)
    subtitles = []
    
    def to_ms(time_str):
        h, m, s = time_str.replace(',', '.').split(':')
        return int(h)*3600000 + int(m)*60000 + float(s)*1000

    for match in matches:
        subtitles.append({
            "start_ms": to_ms(match[1]),
            "end_ms": to_ms(match[2]),
            "text": match[3].strip()
        })
    return subtitles

async def generate_audio(srt_text, voice, rate, pitch):
    subs = parse_srt(srt_text)
    if not subs: return None

    # បង្កើត Timeline ស្ងាត់មួយដែលមានប្រវែងស្មើនឹងម៉ោងបញ្ចប់ចុងក្រោយ + ៥ វិនាទី
    total_len = subs[-1]['end_ms'] + 5000
    final_audio = AudioSegment.silent(duration=total_len)
    
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"

    for i, sub in enumerate(subs):
        # ១. បង្កើតសំឡេង AI ដើម
        communicate = edge_tts.Communicate(sub['text'], voice, rate=rate_str, pitch=pitch_str)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
        
        # ២. គណនារយៈពេលដែលមាន (Available Gap)
        # បើមានឃ្លាបន្ទាប់ យើងត្រូវអានឱ្យចប់មុនឃ្លានោះចាប់ផ្តើម
        if i < len(subs) - 1:
            next_start_ms = subs[i+1]['start_ms']
            available_ms = next_start_ms - sub['start_ms']
        else:
            # ឃ្លាចុងក្រោយ ទុកឱ្យវាអានតាមធម្មជាតិ
            available_ms = len(segment)

        # ៣. ពិនិត្យថាជាន់គ្នាឬអត់? បើជាន់គ្នា ត្រូវពន្លឿន (Speedup)
        # យើងថែមលក្ខខណ្ឌ available_ms > 0 ដើម្បីការពារ Error
        if len(segment) > available_ms and available_ms > 0:
            speed_ratio = len(segment) / available_ms
            # ពន្លឿនតែឃ្លាណាដែលវែងពេក
            segment = segment.speedup(playback_speed=speed_ratio)
        
        # ៤. បញ្ចូលទៅក្នុង Timeline ចំ Start Time នៃ SRT បន្ទាត់នីមួយៗ
        # ការប្រើ position គឺជានាឡិកាវាស់ម៉ោងដែលសុក្រិតបំផុត
        final_audio = final_audio.overlay(segment, position=sub['start_ms'])

    # កាត់ផ្នែកស្ងាត់ចោលវិញក្រោយពេលផលិតរួច
    final_audio = final_audio.strip_silence(silence_thresh=-50, padding=100)

    buffer = io.BytesIO()
    final_audio.export(buffer, format="mp3")
    return buffer.getvalue()

# --- ចំណុចប្រទាក់អ្នកប្រើ (UI) ---
st.title("🎙️ Khmer TTS Smart Precision Sync")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    voice = st.selectbox("សំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
    speed = st.slider("ល្បឿនមូលដ្ឋាន:", -50, 50, 0)
with col2:
    pitch = st.slider("កម្រិតសំឡេង:", -20, 20, 0)
    
srt_input = st.text_area("បញ្ចូល SRT របស់អ្នកនៅទីនេះ:", height=300)

if st.button("🔊 ចាប់ផ្តើមផលិតសំឡេង"):
    if srt_input:
        with st.spinner("កំពុងគណនាម៉ោងឱ្យត្រូវចំវិនាទី..."):
            try:
                result = asyncio.run(generate_audio(srt_input, voice, speed, pitch))
                if result:
                    st.audio(result)
                    st.download_button("📥 ទាញយក MP3", result, "final_sync_audio.mp3")
                    st.success("ផលិតរួចរាល់! សំឡេងនឹងចាប់ផ្តើមត្រូវចំម៉ោង Start Time ជានិច្ច។")
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("សូមបញ្ចូល SRT ជាមុន!")
