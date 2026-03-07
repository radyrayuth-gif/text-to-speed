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
            "end_ms": to_ms(match[2]),
            "text": match[3].replace('\n', ' ').strip()
        })
    return subtitles

def adjust_speed(audio, target_ms):
    """ពន្លឿនសំឡេងឱ្យត្រូវនឹងរយៈពេលក្នុង SRT ប្រសិនបើវាលើស"""
    actual_ms = len(audio)
    if actual_ms <= target_ms or target_ms <= 0:
        return audio
    speed_factor = actual_ms / target_ms
    return audio.speedup(playback_speed=speed_factor, chunk_size=50, crossfade=25)

async def generate_audio(srt_text, voice, rate, pitch):
    subs = parse_srt(srt_text)
    if not subs: return None

    # បង្កើត Timeline ទទេ
    final_audio = AudioSegment.silent(duration=0, frame_rate=44100)
    current_ms = 0
    
    # កំណត់ Format សម្រាប់ Edge TTS
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"

    for sub in subs:
        # ១. ផលិតសំឡេង
        communicate = edge_tts.Communicate(sub['text'], voice, rate=rate_str, pitch=pitch_str)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        # បំប្លែង mp3 ទៅជា AudioSegment
        seg = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3").set_frame_rate(44100)
        
        # ២. គណនាចន្លោះស្ងាត់មុនអាន
        gap_duration = sub['start_ms'] - current_ms
        if gap_duration > 0:
            final_audio += AudioSegment.silent(duration=gap_duration, frame_rate=44100)
            current_ms += gap_duration
        
        # ៣. ឆែកមើលថាតើត្រូវពន្លឿនឱ្យត្រូវនឹង SRT Duration ដែរឬទេ (Auto-fit)
        duration_limit = sub['end_ms'] - sub['start_ms']
        seg = adjust_speed(seg, duration_limit)
        
        # ៤. បញ្ចូលសំឡេងទៅក្នុង Timeline
        final_audio += seg
        current_ms += len(seg)

    buffer = io.BytesIO()
    final_audio.export(buffer, format="mp3")
    return buffer.getvalue()

# --- UI ---
st.title("🎙️ Khmer TTS Precision")

# បង្កើត Sidebar សម្រាប់ Settings ដើម្បីឱ្យទូលាយកន្លែងដាក់ SRT
with st.sidebar:
    st.header("⚙️ ការកំណត់")
    voice_option = st.selectbox("ជ្រើសរើសសំឡេង:", ["km-KH-SreymomNeural", "km-KH-PisethNeural"])
    rate_val = st.slider("ល្បឿននិយាយ (%)", -50, 100, 0, 5)
    pitch_val = st.slider("កម្រិតសំឡេង (Pitch Hz)", -50, 50, 0, 2)
    st.markdown("---")
    st.write("ជំនួយ៖ ល្បឿន 0 គឺធម្មតា")

srt_input = st.text_area("បញ្ចូលអត្ថបទ SRT របស់អ្នក:", height=300, value="""1
00:00:00,700 --> 00:00:02,340
ប្តីសម្លាញ់, ពួកយើងទៅ

2
00:00:03,500 --> 00:00:05,500
តើអ្នកត្រៀមខ្លួនហើយឬនៅ?""")

if st.button("🔊 ផលិតសំឡេងឥឡូវនេះ"):
    with st.spinner("កំពុងផលិតសំឡេង..."):
        try:
            audio_out = asyncio.run(generate_audio(srt_input, voice_option, rate_val, pitch_val))
            if audio_out:
                st.audio(audio_out)
                st.download_button("📥 ទាញយក MP3", audio_out, "khmer_voice.mp3")
        except Exception as e:
            st.error(f"Error: {e}")
