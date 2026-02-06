import streamlit as st
import asyncio
import edge_tts
import re
import io
from pydub import AudioSegment

# --- កំណត់ទំព័រ និងស្ទីល ---
st.set_page_config(page_title="Khmer TTS Pro - លោកពូប៉ាវ", page_icon="🎙️")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stTextArea textarea { font-size: 16px !important; border-radius: 10px; border: 1px solid #28a745; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #28a745; color: white; font-weight: bold; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

# --- មុខងារបំបែកអត្ថបទ SRT ---
def parse_srt(srt_text):
    # ចាប់យកលេខរៀង ម៉ោង និងអត្ថបទ
    pattern = r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\n$|$)"
    matches = re.findall(pattern, srt_text, re.DOTALL)
    
    subtitles = []
    def to_ms(time_str):
        time_str = time_str.replace(',', '.')
        h, m, s = time_str.split(':')
        return int(h)*3600000 + int(m)*60000 + float(s)*1000

    for match in matches:
        subtitles.append({
            "start_ms": to_ms(match[1]),
            "text": match[3].strip()
        })
    return subtitles

# --- មុខងារផលិតសំឡេង ---
async def generate_audio(srt_text, voice, rate, pitch):
    subs = parse_srt(srt_text)
    combined_audio = AudioSegment.empty()
    current_ms = 0 # ម៉ោងបច្ចុប្បន្ននៃខ្សែសំឡេង
    
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"

    for sub in subs:
        # ១. គណនាចន្លោះស្ងាត់ដើម្បីឱ្យចាប់ផ្តើមចំពេលកំណត់
        wait_time = sub['start_ms'] - current_ms
        
        if wait_time > 0:
            # បន្ថែមចន្លោះស្ងាត់រហូតដល់ដល់ម៉ោងត្រូវអាន
            combined_audio += AudioSegment.silent(duration=wait_time)
            current_ms += wait_time
        else:
            # បើ AI អានឃ្លាមុនយឺត ហួសម៉ោងឃ្លាបន្ទាប់ យើងថែមចន្លោះដកដង្ហើមបន្តិច (200ms)
            combined_audio += AudioSegment.silent(duration=200)
            current_ms += 200

        # ២. បង្កើតសំឡេងពី Edge-TTS
        communicate = edge_tts.Communicate(sub['text'], voice, rate=rate_str, pitch=pitch_str)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
        
        # ៣. បញ្ចូលសំឡេងចូលក្នុងខ្សែអាត់ (អានចប់តាមធម្មជាតិ)
        combined_audio += segment
        current_ms += len(segment)

    # បញ្ជូនឯកសារចេញជា Bytes
    buffer = io.BytesIO()
    combined_audio.export(buffer, format="mp3")
    return buffer.getvalue()

# --- ចំណុចប្រទាក់អ្នកប្រើ (UI) ---
st.title("🎙️ Khmer SRT Audio Dubbing (V2)")
st.write("ជំនាន់៖ ចាប់ផ្តើមចំពេល និងអានចប់តាមធម្មជាតិ")

col1, col2 = st.columns([1, 2])

with col1:
    voice_choice = st.selectbox("ជ្រើសរើសអ្នកអាន:", ["ស្រីមុំ (Sreymom)", "ពិសិដ្ឋ (Piseth)"])
    voice_id = "km-KH-SreymomNeural" if "ស្រីមុំ" in voice_choice else "km-KH-PisethNeural"
    img_url = "https://cdn-icons-png.flaticon.com/512/6997/6997662.png" if "ស្រីមុំ" in voice_choice else "https://cdn-icons-png.flaticon.com/512/4128/4128176.png"
    st.image(img_url, width=120)

with col2:
    speed = st.slider("ល្បឿនអាន (%):", -50, 50, 0, 5)
    pitch = st.slider("កម្រិតសំឡេង (Hz):", -20, 20, 0, 1)

srt_input = st.text_area("បញ្ចូលទម្រង់ SRT នៅទីនេះ:", height=250, 
                         placeholder="1\n00:00:01,000 --> 00:00:02,000\nសួស្តីបងប្អូន...")

if st.button("🔊 ចាប់ផ្តើមផលិតសំឡេង"):
    if srt_input.strip():
        with st.spinner("កំពុងរៀបចំតាមកាលវិភាគ..."):
            try:
                final_audio = asyncio.run(generate_audio(srt_input, voice_id, speed, pitch))
                st.audio(final_audio, format="audio/mp3")
                st.download_button("📥 ទាញយក MP3", final_audio, "khmer_audio_sync.mp3")
                st.success("ផលិតរួចរាល់! សំឡេងនឹងចាប់ផ្តើមតាមម៉ោងក្នុង SRT របស់អ្នក។")
            except Exception as e:
                st.error(f"បញ្ហា៖ {e}")
                st.info("ប្រសិនបើឃើញ Error 'ffprobe' សូមប្រាកដថាបានដាក់ 'ffmpeg' ក្នុង packages.txt រួច Reboot App។")
    else:
        st.warning("សូមបញ្ចូលអត្ថបទ SRT ជាមុនសិន!")
