async def generate_audio(srt_text, voice, rate, pitch):
    subs = parse_srt(srt_text)
    combined_audio = AudioSegment.empty()
    current_ms = 0
    
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"

    for sub in subs:
        # ១. គណនាចន្លោះស្ងាត់៖ ឱ្យវាចាប់ផ្តើមចំ Start Time ក្នុង SRT
        silence_duration = sub['start_ms'] - current_ms
        
        if silence_duration > 0:
            # បន្ថែមចន្លោះស្ងាត់បើដល់ពេលត្រូវអាន
            combined_audio += AudioSegment.silent(duration=silence_duration)
            current_ms += silence_duration
        elif silence_duration < 0:
            # បើ AI អានឃ្លាមុនមិនទាន់ចប់ តែដល់ពេលត្រូវអានឃ្លាបន្ទាប់
            # យើងអាចថែមចន្លោះស្ងាត់បន្តិចបន្តួច (ឧទាហរណ៍ 200ms) ដើម្បីកុំឱ្យជាន់គ្នាខ្លាំង
            combined_audio += AudioSegment.silent(duration=200)
            current_ms += 200

        # ២. បង្កើតសំឡេង AI (អានតាមល្បឿនធម្មជាតិដែលអ្នកកំណត់តាម Slider)
        communicate = edge_tts.Communicate(sub['text'], voice, rate=rate_str, pitch=pitch_str)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
        
        # ៣. បញ្ចូលសំឡេងចូលក្នុង Timeline (មិនបាច់កែប្រែ Duration ទេ)
        combined_audio += segment
        
        # ធ្វើបច្ចុប្បន្នភាពពេលវេលាបច្ចុប្បន្ន ក្រោយពេលអានចប់
        current_ms += len(segment)

    buffer = io.BytesIO()
    combined_audio.export(buffer, format="mp3")
    return buffer.getvalue()
