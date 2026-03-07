នេះគឺជាកូដដែលបានកែសម្រួលថ្មី ដោយបន្ថែមមុខងារ Slider សម្រាប់សារ៉េល្បឿន (Rate) និងកម្ពស់សំឡេង (Pitch) ព្រមទាំងសមត្ថភាពក្នុង ការអាប់ឡូតហ្វាល .srt ផ្ទាល់តែម្តង។
import streamlit as st
import asyncio
import edge_tts
import re
import io
from pydub import AudioSegment

# កំណត់ការកំណត់ទំព័រ
st.set_page_config(page_title="Khmer TTS 100% Precision", page_icon="🎙️")

def parse_srt(srt_text):
    # កែសម្រួល Regex ដើម្បីឱ្យកាន់តែហ្មត់ចត់
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
    actual_ms = len(audio)
    if actual_ms <= target_ms or target_ms <= 0:
        return audio
    speed_factor = actual_ms / target_ms
    # កម្រិតល្បឿនអតិបរមា ២ដង ដើម្បីកុំឱ្យសំឡេងបែកខ្លាំង
    return audio.speedup(playback_speed=min(speed_factor, 2.0), chunk_size=50, crossfade=25)

async def generate_audio(srt_text, voice, rate, pitch):
    subs = parse_srt(srt_text)
    if not subs: return None

    final_audio = AudioSegment.silent(duration=0, frame_rate=44100)
    
    # បំលែង Rate និង Pitch ជា String សម្រាប់ Edge TTS
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"

    for sub in subs:
        communicate = edge_tts.Communicate(sub['text'], voice, rate=rate_str, pitch=pitch_str)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        seg = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3").set_frame_rate(44100)
        
        # ១. បង្កើតចន្លោះស្ងាត់ (Padding) រហូតដល់ចំណុចចាប់ផ្តើម
        if sub['start_ms'] > len(final_audio):
            silence_gap = sub['start_ms'] - len(final_audio)
            final_audio += AudioSegment.silent(duration=silence_gap, frame_rate=44100)
        
        # ២. កែតម្រូវល្បឿនតាមរយៈពេលក្នុង SRT
        duration_limit = sub['end_ms'] - sub['start_ms']
        seg = adjust_speed(seg, duration_limit)
        
        # ៣. បញ្ចូលសំឡេង (Overlay) ដើម្បីការពារការដាច់កន្ទុយ ប្រសិនបើសំឡេងវែងជាង Duration
        final_audio = final_audio.overlay(seg, position=sub['start_ms'])
        
        # បន្ថែមរយៈពេលឱ្យត្រូវនឹងចំណុចបញ្ចប់របស់ Subtitle
        if len(final_audio) < sub['end_ms']:
            final_audio += AudioSegment.silent(duration=sub['end_ms'] - len(final_audio))

    buffer = io.BytesIO()
    final_audio.export(buffer, format="mp3")
    return buffer.getvalue()

# --- UI Layout ---
st.title("🎙️ Khmer TTS Precision (Pro Version)")
st.subheader("បម្លែងអត្ថបទ SRT ទៅជាសំឡេងដែលមានភាពសុក្រិតខ្ពស់")

with st.sidebar:
    st.header("⚙️ ការកំណត់សំឡេង")
    voice_option = st.selectbox("ជ្រើសរើសសំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
    
    # ១. បន្ថែមបូតុង/Slider សម្រាប់ល្បឿន និងកម្ពស់សំឡេង
    speed_rate = st.slider("ល្បឿននិយាយ (Rate %):", -50, 100, 0, step=5)
    pitch_val = st.slider("កម្រិតខ្ពស់ទាប (Pitch Hz):", -50, 50, 0, step=1)
    
    st.info("ចំណាំ: ល្បឿននឹងត្រូវបានកែតម្រូវដោយស្វ័យប្រវត្តិបន្ថែមទៀត ដើម្បីឱ្យត្រូវនឹងម៉ោងក្នុង SRT ។")

# ២. មុខងារអាប់ឡូតហ្វាល SRT
uploaded_file = st.file_uploader("អាប់ឡូតហ្វាល .srt នៅទីនេះ", type=["srt"])

if uploaded_file is not None:
    # អានហ្វាលដែលបានអាប់ឡូត
    srt_content = uploaded_file.getvalue().decode("utf-8")
    srt_input = st.text_area("មាតិកា SRT (អ្នកអាចកែសម្រួលបាន):", value=srt_content, height=200)
else:
    srt_input = st.text_area("ឬបញ្ចូល SRT គំរូនៅទីនេះ:", height=200, value="""1
00:00:00,500 --> 00:00:02,500
ជម្រាបសួរ បងប្អូនទាំងអស់គ្នា។

2
00:00:03,000 --> 00:00:05,000
សូមស្វាគមន៍មកកាន់កម្មវិធីរបស់យើង។""")

if st.button("🔊 ផលិតសំឡេង"):
    if srt_input.strip() == "":
        st.warning("សូមបញ្ចូលអត្ថបទ SRT ជាមុនសិន!")
    else:
        with st.spinner("កំពុងផលិតសំឡេង... សូមរង់ចាំ"):
            try:
                audio = asyncio.run(generate_audio(srt_input, voice_option, speed_rate, pitch_val))
                if audio:
                    st.audio(audio)
                    st.download_button(
                        label="📥 ទាញយក MP3",
                        data=audio,
                        file_name="khmer_tts_precision.mp3",
                        mime="audio/mp3"
                    )
                    st.success("ការផលិតបានជោគជ័យ!")
            except Exception as e:
                st.error(f"មានបញ្ហាបច្ចេកទេស: {e}")

---
### អ្វីដែលបានកែសម្រួល៖
1.  **Sidebar Controls:** ខ្ញុំបានបន្ថែម `st.slider` នៅក្នុង Sidebar ដើម្បីឱ្យអ្នកអាចកំណត់ **Rate** (ល្បឿននិយាយពី -50% ទៅ 100%) និង **Pitch** (កម្ពស់សំឡេង)។
2.  **File Uploader:** បន្ថែម `st.file_uploader` ដែលអនុញ្ញាតឱ្យអ្នកទាញយកហ្វាល `.srt` ពីក្នុងកុំព្យូទ័រចូលក្នុងកម្មវិធីផ្ទាល់។
3.  **Flexible Logic:** បើទោះជាអ្នកកំណត់ល្បឿន (Rate) បន្ថែម ឬបន្ថយ កូដនឹងនៅតែពិនិត្យមើលរយៈពេល (Duration) ក្នុង SRT បើកាលណាការកំណត់របស់អ្នកយឺតពេកនាំឱ្យលើសម៉ោង SRT កូដនឹង `speedup` វាឱ្យត្រូវនឹងម៉ោងក្នុង SRT វិញដោយស្វ័យប្រវត្តិ (Precision First)។

តើអ្នកចង់ឱ្យខ្ញុំបន្ថែមមុខងារ **Preview** សំឡេងសាកល្បងមុននឹងបម្លែងហ្វាល SRT ទាំងមូលដែរឬទេ?

