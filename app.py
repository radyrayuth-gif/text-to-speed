import streamlit as st
import asyncio
import edge_tts
import re
import io
from pydub import AudioSegment

st.set_page_config(page_title="Khmer TTS Precision Pro", page_icon="🎙️")

def parse_srt(srt_text):
    # ចាប់យក SRT ឱ្យបានត្រឹមត្រូវ
    pattern = r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\n$|$)"
    matches = re.findall(pattern, srt_text, re.DOTALL)
    subtitles = []
    
    def to_ms(time_str):
        h, m, s = time_str.replace(',', '.').split(':')
        return int(h)*3600000 + int(m)*60000 + float(s)*1000

    for match in matches:
        subtitles.append({
            "start_ms": int(to_ms(match[1])),
            "text": match[3].replace('\n', ' ').strip()
        })
    return subtitles

def change_audio_speed(audio, speed=1.0):
    # ប្តូរល្បឿនដោយរក្សាកម្រិតសំឡេង និងប្រវែងឱ្យសុក្រិត
    if speed == 1.0:
        return audio
    new_sample_rate = int(audio.frame_rate * speed)
    return audio._spawn(audio.raw_data, overrides={'frame_rate': new_sample_rate}).set_frame_rate(audio.frame_rate)

async def generate_audio(srt_text, voice, rate, pitch):
    subs = parse_srt(srt_text)
    if not subs: return None

    # បង្កើត Timeline ទទេរដែលវែងល្មម
    max_time = subs[-1]['start_ms'] + 10000 
    final_audio = AudioSegment.silent(duration=max_time)
    
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
        
        # ២. គណនាម៉ោងដែលមានសម្រាប់ឃ្លានេះ
        if i < len(subs) - 1:
            available_ms = subs[i+1]['start_ms'] - sub['start_ms']
        else:
            available_ms = len(segment)

        # ៣. បើអានវែងពេក ត្រូវពន្លឿនឱ្យល្មមនឹង available_ms
        actual_ms = len(segment)
        if actual_ms > available_ms and available_ms > 0:
            speed_factor = actual_ms / available_ms
            segment = change_audio_speed(segment, speed=speed_factor)
        
        # ៤. បញ្ចូលទៅក្នុង Timeline (ប្រើ Overlay ជាមួយទីតាំងជាក់លាក់)
        final_audio = final_audio.overlay(segment, position=sub['start_ms'])

    # កាត់ផ្នែកស្ងាត់ចោល
    final_audio = final_audio.strip_silence(silence_thresh=-50, padding=100)
    buffer = io.BytesIO()
    final_audio.export(buffer, format="mp3")
    return buffer.getvalue()

# --- UI ---
st.title("🎙️ Khmer TTS: ម៉ោងសុក្រិត ១០០%")
st.write("សំឡេងនឹងចាប់ផ្តើមនៅវិនាទីទី **0.7** និង **20.04** តាម SRT របស់អ្នក។")

col1, col2 = st.columns(2)
with col1:
    voice_choice = st.selectbox("ជ្រើសរើសសំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
    speed_slider = st.slider("ល្បឿនអានទូទៅ:", -50, 50, 0)
with col2:
    pitch_slider = st.slider("កម្រិតសំឡេង:", -20, 20, 0)

srt_input = st.text_area("បញ្ចូល SRT:", height=200, value="""1
00:00:00,700 --> 00:00:02,340
ប្តីសម្លាញ់, ពួកយើងទៅ

2
00:00:20,040 --> 00:00:21,840
បួងសួងឱ្យពេលវេលាកន្លងផុតទៅ

3
00:00:21,840 --> 00:00:24,160
ការចាកចេញរបស់ខ្ញុំក៏បានបញ្ចប់""")

if st.button("🔊 ផលិតសំឡេងឥឡូវនេះ"):
    with st.spinner("កំពុងរៀបចំតាមវិនាទី..."):
        try:
            audio_out = asyncio.run(generate_audio(srt_input, voice_choice, speed_slider, pitch_slider))
            if audio_out:
                st.audio(audio_out)
                st.download_button("📥 ទាញយក", audio_out, "precision_voice.mp3")
        except Exception as e:
            st.error(f"បញ្ហា៖ {e}")
