import streamlit as st
import asyncio
import edge_tts
import re
import io
from pydub import AudioSegment

# --- កំណត់ទំព័រ ---
st.set_page_config(page_title="Khmer TTS Smart Sync", page_icon="🎙️")

def parse_srt(srt_text):
    pattern = r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\n$|$)"
    matches = re.findall(pattern, srt_text, re.DOTALL)
    subtitles = []
    def to_ms(time_str):
        h, m, s = time_str.replace(',', '.').split(':')
        return int(h)*3600000 + int(m)*60000 + float(s)*1000
    for match in matches:
        subtitles.append({
            "start_ms": to_ms(match[1]),
            "end_ms": to_ms(match[2]), # ប្រើសម្រាប់ប៉ាន់ស្មានម៉ោងបញ្ចប់
            "text": match[3].strip()
        })
    return subtitles

async def generate_audio(srt_text, voice, rate, pitch):
    subs = parse_srt(srt_text)
    if not subs: return None

    total_duration_ms = subs[-1]['start_ms'] + 10000 
    final_combined = AudioSegment.silent(duration=total_duration_ms)
    
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"

    for i in range(len(subs)):
        sub = subs[i]
        
        # ១. បង្កើតសំឡេង AI ដើម
        communicate = edge_tts.Communicate(sub['text'], voice, rate=rate_str, pitch=pitch_str)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio": audio_data += chunk["data"]
        
        segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
        
        # ២. ពិនិត្យមើលការជាន់គ្នា (Overlap Detection)
        # បើមិនមែនជាឃ្លាចុងក្រោយ យើងមើលម៉ោងចាប់ផ្តើមនៃឃ្លាបន្ទាប់
        if i < len(subs) - 1:
            next_start_ms = subs[i+1]['start_ms']
            available_duration = next_start_ms - sub['start_ms']
            actual_duration = len(segment)
            
            # បើអានវែងជាងម៉ោងដែលត្រូវចាប់ផ្តើមឃ្លាបន្ទាប់ (ជាន់គ្នា)
            if actual_duration > available_duration and available_duration > 0:
                speed_factor = actual_duration / available_duration
                # ពន្លឿនសំឡេងតែឃ្លានេះឱ្យចប់ទាន់ពេល
                segment = segment.speedup(playback_speed=speed_factor)
        
        # ៣. ដាក់ចូល Timeline
        final_combined = final_combined.overlay(segment, position=sub['start_ms'])

    # កាត់ផ្នែកស្ងាត់កន្ទុយចោល
    final_combined = final_combined.strip_silence(silence_thresh=-50, padding=100)
    
    buffer = io.BytesIO()
    final_combined.export(buffer, format="mp3")
    return buffer.getvalue()

# --- UI ---
st.title("🎙️ Khmer TTS Smart Speed Sync")
st.info("💡 ឃ្លាណាដែលអានជាន់គ្នា នឹងត្រូវបានពន្លឿនដោយស្វ័យប្រវត្តិឱ្យចប់ទាន់ពេល។")

voice_choice = st.selectbox("ជ្រើសរើសអ្នកអាន:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
speed_val = st.slider("ល្បឿនមូលដ្ឋាន (%):", -50, 50, 0, 5)
pitch_val = st.slider("កម្រិតសំឡេង (Hz):", -20, 20, 0, 1)
srt_input = st.text_area("បញ្ចូល SRT:", height=250)

if st.button("🔊 ផលិតសំឡេង"):
    if srt_input.strip():
        with st.spinner("កំពុងគណនា និងកែតម្រូវល្បឿន..."):
            try:
                final_audio = asyncio.run(generate_audio(srt_input, voice_choice, speed_val, pitch_val))
                st.audio(final_audio)
                st.download_button("📥 ទាញយក MP3", final_audio, "smart_sync.mp3")
            except Exception as e:
                st.error(f"បញ្ហា៖ {e}")
                
