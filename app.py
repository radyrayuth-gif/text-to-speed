import streamlit as st
import google.generativeai as genai
import re

# ការកំណត់រូបរាង Website
st.set_page_config(page_title="SRT Chinese to Khmer Translator", layout="centered")
st.title("🏯 ឧបករណ៍បកប្រែរឿងភាគចិន (SRT)")
st.subheader("បកប្រែដោយប្រើ Gemini AI")

# កន្លែងដាក់ API Key
api_key = st.sidebar.text_input("បញ្ចូល Gemini API Key របស់អ្នក:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # កន្លែងបញ្ចូលអត្ថបទ
    source_text = st.text_area("បញ្ចូលអត្ថបទចិន (ទម្រង់ SRT):", height=300, placeholder="1\n00:00:00,000 --> ...")

    if st.button("ចាប់ផ្តើមបកប្រែ"):
        if source_text.strip() == "":
            st.warning("សូមបញ្ចូលអត្ថបទជាមុនសិន!")
        else:
            try:
                with st.spinner('កំពុងបកប្រែ... សូមរង់ចាំ'):
                    # បង្កើត Prompt ដើម្បីប្រាប់ AI ឲ្យរក្សាទម្រង់លេខរៀង និងម៉ោង
                    prompt = f"""
                    You are a professional translator. Translate the following Chinese SRT subtitles into Khmer.
                    Keep the subtitle numbers and timestamps exactly as they are. 
                    Ensure the Khmer translation is natural for storytelling/movies.
                    
                    Text to translate:
                    {source_text}
                    """
                    
                    response = model.generate_content(prompt)
                    
                    st.success("ការបកប្រែរួចរាល់!")
                    st.text_area("លទ្ធផលជាភាសាខ្មែរ:", value=response.text, height=300)
                    
                    # ប៊ូតុងទាញយក
                    st.download_button(
                        label="ទាញយកឯកសារ .srt",
                        data=response.text,
                        file_name="translated_khmer.srt",
                        mime="text/plain"
                    )
            except Exception as e:
                st.error(f"មានបញ្ហាបច្ចេកទេស៖ {e}")
else:
    st.info("សូមបញ្ចូល Gemini API Key នៅផ្នែកខាងឆ្វេង (Sidebar) ដើម្បីចាប់ផ្តើម។")
