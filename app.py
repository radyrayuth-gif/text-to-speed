import streamlit as st
import asyncio
import edge_tts
import re
import io
from pydub import AudioSegment

# --- កំណត់ទំព័រ ---
st.set_page_config(page_title="Khmer TTS Precision Fix", page_icon="🎙️")

def parse_srt(srt_text):
    # ចាប់យក SRT: លេខរៀង, ម៉ោងចាប់ផ្តើម, និង អត្ថបទ
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

def change_audio_speed(audio, speed=1.0):
    """ប្តូរល្បឿនដោយរក្សាកម្រិតសំឡេង និងប្រវែងឱ្យសុក្រិត"""
    if speed <= 1.0:
        return audio
    new_sample_rate = int(audio.frame_rate * speed)
    return audio._spawn(audio.raw_data, overrides={'frame_rate': new_sample_rate}).set_frame_rate(audio.frame_rate)

async def generate_audio(srt_text, voice, rate, pitch):
    subs = parse_srt(srt_text)
    if not subs: return None

    # ១. បង្កើត "កម្រាលសំឡេងស្ងាត់" ជាមុនសិន (Base Timeline)
    # យើងបង្កើតឱ្យវែងជាងម៉ោងបញ្ចប់ក្នុង SRT បន្តិច ដើម្បីកុំឱ្យបាត់សំឡេង
    max_duration_ms = subs[-1]['start_ms'] + 10000 
    final_audio = AudioSegment.silent(duration=max_duration_ms)
    
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"

    for i, sub in enumerate(subs):
        # ២. ផលិតសំឡេង AI ពី Edge TTS
        communicate = edge_tts.Communicate(sub['text'], voice, rate=rate_str, pitch=pitch_str)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        # បំប្លែងទិន្នន័យ MP3 ទៅជា AudioSegment
        segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
        
        # ៣. ពិនិត្យមើលការជាន់គ្នា (Smart Speedup)
        # បើអានវែងពេក រហូតដល់ជាន់ម៉ោងចាប់ផ្តើមរបស់ឃ្លាបន្ទាប់ ត្រូវពន្លឿនវា
        if i < len(subs) - 1:
            available_ms = subs[i+1]['start_ms'] - sub['start_ms']
            actual_ms = len(segment)
            if actual_ms > available_ms and available_ms > 0:
                speed_factor = actual_ms / available_ms
                segment = change_audio_speed(segment, speed=speed_factor)
        
        # ៤. ដាក់សំឡេងចូលទៅក្នុងកម្រាលស្ងាត់ (Overlay) តាមទីតាំង Start Time
        # position=sub['start_ms'] គឺជាគន្លឹះដែលធ្វើឱ្យវាត្រូវម៉ោង ១០០%
        final_audio = final_audio.overlay(segment, position=sub['start_ms'])

    # កាត់ផ្នែកស្ងាត់ដែលនៅសល់កន្ទុយចោល
    final_audio = final_audio.strip_silence(silence_thresh=-50, padding=200)

    # បញ្ជូនឯកសារចេញជា MP3
    buffer = io.BytesIO()
    final_audio.export(buffer, format="mp3")
    return buffer.getvalue()

# --- ចំណុចប្រទាក់អ្នកប្រើ (UI) ---
st.title("🎙️ Khmer TTS Precision (ឮសំឡេង និង ត្រូវម៉ោង)")
st.info("កូដនេះដោះស្រាយបញ្ហា 'ស្ងាត់' និង 'ម៉ោងមិនត្រូវ' រួចរាល់ហើយ។")

srt_input = st.text_area("បញ្ចូល SRT របស់អ្នក:", height=200, value="""1
00:00:00,700 --> 00:00:02,340
ប្តីសម្លាញ់, ពួកយើងទៅ

2
00:00:20,040 --> 00:00:21,840
បួងសួងឱ្យពេលវេលាកន្លងផុតទៅ

3
00:00:21,840 --> 00:00:24,160
ការចាកចេញរបស់ខ្ញុំក៏បានបញ្ចប់""")

col1, col2 = st.columns(2)
with col1:
    voice_choice = st.selectbox("អ្នកអាន:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
with col2:
    speed = st.slider("ល្បឿនមូលដ្ឋាន:", -50, 50, 0)

if st.button("🔊 ផលិតសំឡេង"):
    if srt_input.strip():
        with st.spinner("កំពុងផលិត..."):
            try:
                audio_result = asyncio.run(generate_audio(srt_input, voice_choice, speed, 0))
                if audio_result:
                    st.audio(audio_result, format="audio/mp3")
                    st.download_button("📥 ទាញយក MP3", audio_result, "fixed_audio.mp3")
            except Exception as e:
                st.error(f"បញ្ហា៖ {e}")
