នេះគឺជាកូដដែលបានកែសម្រួល ដោយបន្ថែម Slider សម្រាប់ឱ្យអ្នកប្រើប្រាស់អាចសារ៉េ ល្បឿន (Rate) និង កម្រិតសំឡេង (Pitch) បានដោយខ្លួនឯងតាមតម្រូវការ៖
import streamlit as st
import asyncio
import edge_tts
import re
import io
from pydub import AudioSegment

st.set_page_config(page_title="Khmer TTS 100% Precision", page_icon="🎙️")

def parse_srt(srt_text):
    # Pattern សម្រាប់ចាប់យក SRT format
    pattern = r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\n$|$)"
    matches = re.findall(pattern, srt_text, re.DOTALL)
    subtitles = []
    
    def to_ms(time_str):
        h, m, s = time_str.replace(',', '.').split(':')
        return int(int(h)*3600000 + int(m)*60000 + float(s)*1000)

    for match in matches:
        subtitles.append({
            "start_ms": to_ms(match[1]),
            "end_ms": to_ms(match[2]),
            "text": match[3].replace('\n', ' ').strip()
        })
    return subtitles

def adjust_speed(audio, target_ms):
    """ពន្លឿនសំឡេងឱ្យត្រូវនឹងរយៈពេលដែលកំណត់ក្នុង SRT ប្រសិនបើវាវែងពេក"""
    actual_ms = len(audio)
    if actual_ms <= target_ms or target_ms <= 0:
        return audio
    speed_factor = actual_ms / target_ms
    # កំណត់ speedup ឱ្យសមស្រប (មិនឱ្យញ័រខ្លាំង)
    return audio.speedup(playback_speed=speed_factor, chunk_size=50, crossfade=25)

async def generate_audio(srt_text, voice, rate, pitch):
    subs = parse_srt(srt_text)
    if not subs: return None

    # បង្កើតសំឡេងស្ងាត់ជាមូលដ្ឋាន
    final_audio = AudioSegment.silent(duration=0, frame_rate=44100)
    
    # បំលែងតម្លៃ Rate និង Pitch ទៅជា String សម្រាប់ Edge TTS
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"

    for sub in subs:
        # ១. ផលិតសំឡេងចេញពី Edge TTS
        communicate = edge_tts.Communicate(sub['text'], voice, rate=rate_str, pitch=pitch_str)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        # បំប្លែងទៅជា AudioSegment
        seg = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3").set_frame_rate(44100)
        
        # ២. គណនាចន្លោះស្ងាត់មុនអាន (Padding)
        # បង្កើតចន្លោះស្ងាត់រហូតដល់វិនាទីដែលត្រូវចាប់ផ្តើម
        silence_needed = sub['start_ms'] - len(final_audio)
        if silence_needed > 0:
            final_audio += AudioSegment.silent(duration=silence_needed, frame_rate=44100)
        
        # ៣. កែតម្រូវល្បឿនឱ្យត្រូវនឹង SRT duration (Autofit)
        duration_limit = sub['end_ms'] - sub['start_ms']
        seg = adjust_speed(seg, duration_limit)
        
        # ៤. បញ្ចូលសំឡេងទៅក្នុង Timeline
        # ប្រើ overlay ដើម្បីធានាថាវានៅចំទីតាំង Start_ms ជានិច្ច
        final_audio = final_audio.overlay(seg, position=sub['start_ms'])

    buffer = io.BytesIO()
    final_audio.export(buffer, format="mp3")
    return buffer.getvalue()

# --- UI ---
st.title("🎙️ Khmer TTS Precision (Enhanced)")
st.subheader("ឧបករណ៍បំប្លែងអត្ថបទទៅជាសំឡេងតាមកាលវិភាគ SRT")

# ចំហៀងចំហៀងសម្រាប់កំណត់ Settings
col1, col2 = st.columns([2, 1])

with col2:
    st.write("⚙️ **ការកំណត់សំឡេង**")
    voice_option = st.selectbox("ជ្រើសរើសសំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
    
    # បូតុងសម្រាប់កំណត់ល្បឿន (Rate)
    rate_val = st.slider("ល្បឿននិយាយ (%)", min_value=-50, max_value=100, value=0, step=5)
    
    # បូតុងសម្រាប់កំណត់កម្ពស់សំឡេង (Pitch)
    pitch_val = st.slider("កម្រិតសំឡេង (Pitch Hz)", min_value=-50, max_value=50, value=0, step=2)
    
    st.info("💡 ល្បឿន (+) ធ្វើឱ្យនិយាយលឿន, (-) ធ្វើឱ្យនិយាយយឺត។")

with col1:
    srt_input = st.text_area("បញ្ចូលកូដ SRT របស់អ្នកទីនេះ:", height=300, value="""1
00:00:00,700 --> 00:00:02,340
ប្តីសម្លាញ់, ពួកយើងទៅ

2
00:00:03,500 --> 00:00:05,500
តើអ្នកត្រៀមខ្លួនហើយឬនៅ?

3
00:00:06,000 --> 00:00:08,500
ពួកយើងនឹងធ្វើដំណើរទៅជាមួយគ្នា""")

if st.button("🔊 ផលិតសំឡេង និងទាញយក"):
    if srt_input.strip() == "":
        st.warning("សូមបញ្ចូលអត្ថបទ SRT ជាមុនសិន!")
    else:
        with st.spinner("កំពុងផលិតសំឡេង... សូមរង់ចាំ"):
            try:
                audio_bytes = asyncio.run(generate_audio(srt_input, voice_option, rate_val, pitch_val))
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3")
                    st.download_button(
                        label="📥 ទាញយកឯកសារ MP3",
                        data=audio_bytes,
                        file_name="khmer_tts_precision.mp3",
                        mime="audio/mp3"
                    )
            except Exception as e:
                st.error(f"មានបញ្ហាបច្ចេកទេស: {e}")

-
