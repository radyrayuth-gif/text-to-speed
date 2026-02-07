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
    """ពន្លឿនសំឡេងឱ្យត្រូវនឹងរយៈពេលដែលកំណត់ក្នុង SRT"""
    actual_ms = len(audio)
    if actual_ms <= target_ms or target_ms <= 0:
        return audio
    speed_factor = actual_ms / target_ms
    return audio.speedup(playback_speed=speed_factor, chunk_size=50, crossfade=25)

async def generate_audio(srt_text, voice, rate, pitch):
    subs = parse_srt(srt_text)
    if not subs: return None

    # បង្កើតសំឡេងស្ងាត់ជាមូលដ្ឋាន (៤៤.១ kHz ដើម្បីភាពសុក្រិត)
    final_audio = AudioSegment.silent(duration=0, frame_rate=44100)
    current_ms = 0
    
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"

    for i, sub in enumerate(subs):
        # ១. ផលិតសំឡេង
        communicate = edge_tts.Communicate(sub['text'], voice, rate=rate_str, pitch=pitch_str)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        # បំប្លែង និងកំណត់ Frame Rate ឱ្យស្មើគ្នាទាំងអស់
        seg = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3").set_frame_rate(44100)
        
        # ២. គណនាចន្លោះស្ងាត់មុនអាន
        gap_duration = sub['start_ms'] - current_ms
        
        if gap_duration > 0:
            final_audio += AudioSegment.silent(duration=gap_duration, frame_rate=44100)
            current_ms += gap_duration
        
        # ៣. កែតម្រូវល្បឿនឱ្យត្រូវនឹងចន្លោះពេល Start ទៅ End របស់វា
        duration_limit = sub['end_ms'] - sub['start_ms']
        seg = adjust_speed(seg, duration_limit)
        
        # ៤. បញ្ចូលសំឡេងចូលទៅក្នុង Timeline
        # ប្រើ overlay ក្នុងករណីមានការជាន់គ្នាខ្លាំង ប៉ុន្តែប្រើការបូក (+) សម្រាប់ភាពសុក្រិតធម្មតា
        if sub['start_ms'] < len(final_audio):
             final_audio = final_audio.overlay(seg, position=sub['start_ms'])
        else:
             final_audio += seg
        
        # កំណត់ម៉ោងបច្ចុប្បន្នឡើងវិញតាម SRT
        current_ms = sub['start_ms'] + len(seg)

    buffer = io.BytesIO()
    final_audio.export(buffer, format="mp3")
    return buffer.getvalue()

# --- UI ---
st.title("🎙️ Khmer TTS Precision (Final Version)")
st.markdown("---")

srt_input = st.text_area("បញ្ចូល SRT របស់អ្នក:", height=200, value="""1
00:00:00,700 --> 00:00:02,340
ប្តីសម្លាញ់, ពួកយើងទៅ

2
00:00:20,040 --> 00:00:21,840
បួងសួងឱ្យពេលវេលាកន្លងផុតទៅ

3
00:00:21,840 --> 00:00:24,160
ការចាកចេញរបស់ខ្ញុំក៏បានបញ្ចប់""")

if st.button("🔊 ផលិតសំឡេង"):
    with st.spinner("កំពុងដំណើរការ..."):
        try:
            audio = asyncio.run(generate_audio(srt_input, "km-KH-SreymomNeural", 0, 0))
            st.audio(audio)
            st.download_button("ទាញយក MP3", audio, "precision_fix.mp3")
        except Exception as e:
            st.error(f"Error: {e}")
