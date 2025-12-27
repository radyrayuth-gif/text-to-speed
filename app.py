import streamlit as st
import asyncio
import edge_tts
import os
st.set_page_config(page_title="Khmer AI Voice", page_icon="🎙️")
st.title("🎙️ Khmer AI Voice Pro")
# បង្កើត Folder បណ្ដោះអាសន្នសម្រាប់ទុក File សំឡេង
if not os.path.exists("temp"):
    os.makedirs("temp")
text = st.text_area("បញ្ចូលអត្ថបទខ្មែរ៖", "សួស្តី! តើអ្នកសុខសប្បាយជាទេ?")
async def generate_voice(text_input):
    # ប្រើសំឡេងស្រីមុំ (Sreymom)
    communicate = edge_tts.Communicate(text_input, "km-KH-SreymomNeural")
    await communicate.save("temp/output.mp3")
if st.button("បំប្លែងជាសំឡេង"):
    if text:
        with st.spinner('កំពុងដំណើរការ...'):
            asyncio.run(generate_voice(text))
            audio_file = open("temp/output.mp3", "rb")
            st.audio(audio_file.read(), format="audio/mp3")
            st.success("ជោគជ័យ!")
    else:
        st.error("សូមបញ្ចូលអត្ថបទ!")
