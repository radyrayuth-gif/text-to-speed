import streamlit as st
import asyncio
import edge_tts
import re
import io
from pydub import AudioSegment

# --- កំណត់ទំព័រ ---
st.set_page_config(page_title="Khmer TTS Pro - លោកពូប៉ាវ", page_icon="🎙️")

def parse_srt(srt_text):
    """បំបែក SRT ទៅជាបញ្ជីអត្ថបទ និងពេលវេលា"""
    # Pattern សម្រាប់ចាប់យកលំដាប់ ម៉ោងចាប់ផ្តើម ម៉ោងបញ្ចប់ និងអត្ថបទ
    pattern = r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\n$|$)"
    matches = re.findall(pattern, srt_text, re.DOTALL)
    subtitles = []
    for match in matches:
        start_time = match[1].replace(',', '.')
        end_time = match[2].replace(',', '.')
        
        # បំប្លែងម៉ោងចាប់ផ្តើម និងបញ្ចប់ ទៅជាមីលីវិនាទី (ms)
        def to_ms(time_str):
            h, m, s = time_str.split(':')
            return int(h)*3600000 + int(m)*60000 + float(s)*1000

        subtitles.append({
            "start_ms": to_ms(start_time),
            "end_ms": to_ms(end_time),
            "text": match[3].replace('\n', ' ')
        })
    return subtitles

async def generate_audio(srt_text, voice, rate, pitch):
    subs = parse_srt(srt_text)
    combined_audio = AudioSegment.empty()
    
    # បង្កើតសំឡេងស្ងាត់ដំបូង (ប្រសិនបើ SRT មិនចាប់ផ្តើមពីវិនាទីទី ០)
    current_ms = 0
    
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"

    for sub in subs:
        # ១. ថែមចន្លោះស្ងាត់មុនពេលអានឃ្លានេះ
        silence_duration = sub['start_ms'] - current_ms
        if silence_duration > 0:
            combined_audio += AudioSegment.silent(duration=silence_duration)
        
        # ២. បង្កើតសំឡេង AI
        communicate = edge_tts.Communicate(sub['text'], voice, rate=rate_str, pitch=pitch_str)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
        
        # ៣. ពិនិត្យរយៈពេលអាន៖ ប្រសិនបើ AI អានវែងជាងម៉ោងបញ្ចប់ក្នុង SRT
        target_duration = sub['end_ms'] - sub['start_ms']
        actual_duration = len(segment)
        
        if actual_duration > target_duration and target_duration > 0:
            # ពន្លឿនសំឡេងបន្តិច ដើម្បីឱ្យចប់ត្រឹមម៉ោងដែលបានកំណត់
            speed_factor = actual_duration / target_duration
            segment = segment._spawn(segment.raw_data, overrides={
                "frame_rate": int(segment.frame_rate * speed_factor)
            }).set_frame_rate(segment.frame_rate)
        
        combined_audio += segment
        current_ms = sub['start_ms'] + len(segment)

    buffer = io.BytesIO()
    combined_audio.export(buffer, format="mp3")
    return buffer.getvalue()

# --- ចំណុចប្រទាក់អ្នកប្រើ (UI) រក្សាដូចដើម ---
st.title("🎙️ កម្មវិធីអានតាមម៉ោង SRT")
st.write("ជំនាន់កែសម្រួលម៉ោងឱ្យត្រូវ ១០០%")

# (កូដ UI ផ្សេងៗដូចជា selectbox, slider, text_area និង button សូមរក្សាទុកដូចមុន)
# ... ចម្លង UI ពីកូដចាស់មកដាក់ទីនេះ ...
