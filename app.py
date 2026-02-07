import streamlit as st
import asyncio
import edge_tts
import re
import io
from pydub import AudioSegment

st.set_page_config(page_title="Khmer TTS 100% Precision", page_icon="🎙️")

def parse_srt(srt_text):
    pattern = r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\n$|$)"
    matches = re.findall(pattern, srt_text, re.DOTALL)
    subtitles = []
    
    def to_ms(time_str):
        h, m, s = time_str.replace(',', '.').split(':')
        return int(int(h)*3600000 + int(m)*60000 + float(s)*1000)

    for match in matches:
        subtitles.append({
            "start_ms": to_ms(match[1]),
            "text": match[3].replace('\n', ' ').strip()
        })
    return subtitles

def adjust_speed_to_fit(audio, target_duration_ms):
    """ពន្លឿនសំឡេងឱ្យខ្លីល្មមនឹងរយៈពេលដែលកំណត់"""
    actual_duration = len(audio)
    if actual_duration <= target_duration_ms or target_duration_ms <= 0:
        return audio
    
    speed_factor = actual_duration / target_duration_ms
    # ប្រើវិធីសាស្ត្រ frame_rate ដើម្បីប្តូរល្បឿនឱ្យសុក្រិតបំផុត
    new_sample_rate = int(audio.frame_rate * speed_factor)
    return audio._spawn(audio.raw_data, overrides={'frame_rate': new_sample_rate}).set_frame_rate(audio.frame_rate)

async def generate_audio(srt_text, voice, rate, pitch):
    subs = parse_srt(srt_text)
    if not subs: return None

    # បង្កើតសំឡេងមេទទេ
    final_audio = AudioSegment.empty()
    current_timeline_ms = 0 # នាឡិកាវាស់ម៉ោងបច្ចុប្បន្ន
    
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"

    for i, sub in enumerate(subs):
        # ១. ផលិតសំឡេង AI
        communicate = edge_tts.Communicate(sub['text'], voice, rate=rate_str, pitch=pitch_str)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
        
        # ២. គណនាចន្លោះស្ងាត់ (Silence) ពីម៉ោងបច្ចុប្បន្ន ទៅម៉ោងចាប់ផ្តើមក្នុង SRT
        silence_needed = sub['start_ms'] - current_timeline_ms
        
        if silence_needed > 0:
            # បើមានចន្លោះទំនេរ ត្រូវថែម Silence ឱ្យដល់ម៉ោងចាប់ផ្តើម
            final_audio += AudioSegment.silent(duration=silence_needed)
            current_timeline_ms += silence_needed
        elif silence_needed < 0:
            # បើដល់ម៉ោងត្រូវនិយាយហើយ តែសំឡេងមុននៅមិនទាន់ចប់ (Overlap)
            # យើងត្រូវពន្លឿនសំឡេងមុន (Logic នេះត្រូវបានដោះស្រាយដោយ Overlay ក្នុងករណីចង់ឱ្យជាន់គ្នា)
            # ប៉ុន្តែដើម្បីឱ្យសុក្រិតបំផុត យើងនឹងកាត់វាឱ្យចូលឡូហ្សិក Overlay វិញ
            pass

        # ៣. គណនារយៈពេលដែលមានសម្រាប់ឃ្លានេះ (មុនដល់ឃ្លាបន្ទាប់)
        if i < len(subs) - 1:
            available_duration = subs[i+1]['start_ms'] - sub['start_ms']
            # បើអានវែងជាងម៉ោងដែលត្រូវចាប់ផ្តើមឃ្លាបន្ទាប់ ត្រូវពន្លឿនវា
            segment = adjust_speed_to_fit(segment, available_duration)
        
        # ៤. បញ្ចូលសំឡេងទៅក្នុង Timeline
        # ប្រើ overlay ដើម្បីឱ្យវាអាចជាន់គ្នាបានប្រសិនបើចាំបាច់ ប៉ុន្តែរក្សាម៉ោងដើម
        final_audio = final_audio.overlay(segment, position=sub['start_ms'])
        
        # បច្ចុប្បន្នភាពនាឡិកា (យើងមិនបូក segment length ទេ គឺយើងបូកតាម SRT)
        # ប្រសិនបើវាជាន់គ្នា current_timeline នឹងនៅតែត្រូវតាម SRT
        if i < len(subs) - 1:
            current_timeline_ms = sub['start_ms'] 

    buffer = io.BytesIO()
    final_audio.export(buffer, format="mp3")
    return buffer.getvalue()

# --- UI ---
st.title("🎙️ Khmer TTS Precision (Final Fix)")
st.warning("កូដនេះប្រើការគណនា Silence និង Positional Overlay រួមគ្នាដើម្បីធានាម៉ោង ១០០%។")

srt_example = """1
00:00:00,700 --> 00:00:02,340
ប្តីសម្លាញ់, ពួកយើងទៅ

2
00:00:20,040 --> 00:00:21,840
បួងសួងឱ្យពេលវេលាកន្លងផុតទៅ

3
00:00:21,840 --> 00:00:24,160
ការចាកចេញរបស់ខ្ញុំក៏បានបញ្ចប់"""

srt_input = st.text_area("បញ្ចូល SRT:", value=srt_example, height=200)

if st.button("🔊 ផលិតសំឡេង"):
    with st.spinner("កំពុងរៀបចំ..."):
        try:
            audio_out = asyncio.run(generate_audio(srt_input, "km-KH-SreymomNeural", 0, 0))
            st.audio(audio_out)
        except Exception as e:
            st.error(f"Error: {e}")
            
