import streamlit as st
import asyncio
import edge_tts
import re
import io
from pydub import AudioSegment

# --- កំណត់ទំព័រ ---
st.set_page_config(page_title="Khmer TTS Pro - លោកពូប៉ាវ", page_icon="🎙️")

# ស្ទីល UI បន្ថែម
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stTextArea textarea { font-size: 16px !important; border: 2px solid #28a745; }
    .stButton>button { background-color: #28a745; color: white; border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- មុខងារបំបែកអត្ថបទ SRT ---
def parse_srt(srt_text):
    # ចាប់យកលេខរៀង ម៉ោងចាប់ផ្តើម និងអត្ថបទ
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

# --- មុខងារផលិតសំឡេង (បច្ចេកទេស Overlap) ---
async def generate_audio(srt_text, voice, rate, pitch):
    subs = parse_srt(srt_text)
    
    # បង្កើតខ្សែសំឡេងមេមួយ (Silence) ដែលមានរយៈពេលវែងគ្រាន់
    # យើងប្រើ overlay ដើម្បីដាក់សំឡេងចូលទៅតាមម៉ោងជាក់លាក់
    final_combined = AudioSegment.silent(duration=0)
    
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"

    for sub in subs:
        # ១. បង្កើតសំឡេង AI សម្រាប់ឃ្លានីមួយៗ
        communicate = edge_tts.Communicate(sub['text'], voice, rate=rate_str, pitch=pitch_str)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
        
        # ២. កំណត់ទីតាំងសម្រាប់ឃ្លានេះ
        # បង្កើត Silence រហូតដល់ដល់ម៉ោងចាប់ផ្តើម រួចទើបបូកសំឡេងឃ្លានោះចូល
        start_at_ms = sub['start_ms']
        entry_with_start_delay = AudioSegment.silent(duration=start_at_ms) + segment
        
        # ៣. ប្រើ Overlay ដើម្បីឱ្យសំឡេងអាចជាន់គ្នាបាន
        # វានឹងចាប់ផ្តើមចំពេលដែលកំណត់ ទោះបីឃ្លាមុនអានមិនទាន់ចប់ក៏ដោយ
        final_combined = final_combined.overlay(entry_with_start_delay)

    # បញ្ជូនឯកសារចេញ
    buffer = io.BytesIO()
    final_combined.export(buffer, format="mp3")
    return buffer.getvalue()

# --- ចំណុចប្រទាក់អ្នកប្រើ (UI) ---
st.title("🎙️ Khmer SRT Audio (Strict Start & Overlap)")
st.write("ជំនាន់ពិសេស៖ ចាប់ផ្តើមចំពេលកំណត់ និងអាចអានជាន់គ្នាបាន")

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
        with st.spinner("កំពុងរៀបចំ Timeline ឱ្យចំវិនាទី..."):
            try:
                final_audio = asyncio.run(generate_audio(srt_input, voice_id, speed, pitch))
                st.audio(final_audio, format="audio/mp3")
                st.download_button("📥 ទាញយក MP3", final_audio, "khmer_strict_sync.mp3")
                st.success("ផលិតជោគជ័យ! សំឡេងនីមួយៗចាប់ផ្តើមចំពេលកំណត់ក្នុង SRT។")
            except Exception as e:
                st.error(f"បញ្ហា៖ {e}")
    else:
        st.warning("សូមបញ្ចូលអត្ថបទ SRT ជាមុនសិន!")
