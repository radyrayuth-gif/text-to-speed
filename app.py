import streamlit as st
import google.generativeai as genai
import os

# ១. កំណត់ទម្រង់ Website
st.set_page_config(page_title="SRT Chinese-Khmer Translator", layout="wide")
st.title("🏯 ឧបករណ៍បកប្រែ Subtitle ចិន-ខ្មែរ")
st.markdown("---")

# ២. ការបញ្ចូល API Key តាមរយៈ Sidebar
st.sidebar.header("⚙️ ការកំណត់")
user_api_key = st.sidebar.text_input("បញ្ចូល Gemini API Key:", type="password")

# ៣. មុខងារបកប្រែ
def translate_srt(text, api_key):
    # កំណត់ការប្រើប្រាស់ API
    genai.configure(api_key=api_key)
    
    # បង្កើត Model (ប្រើឈ្មោះផ្លូវការដើម្បីជៀសវាង Error 404)
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    
    # Prompt បញ្ជាឱ្យបកប្រែ និងរក្សាទម្រង់ SRT
    prompt = f"""
    Translate the following Chinese SRT subtitles into natural Khmer language.
    Strict Instructions:
    - Keep all timestamps (e.g., 00:00:01,000 --> 00:00:02,000) and subtitle numbers exactly as they are.
    - Only output the translated SRT content.
    - Translation should be natural for a movie context.
    
    Content:
    {text}
    """
    
    response = model.generate_content(prompt)
    return response.text

# ៤. រចនាសម្ព័ន្ធ UI សម្រាប់ការបញ្ចូល និងបង្ហាញលទ្ធផល
col1, col2 = st.columns(2)

with col1:
    st.subheader("📥 អត្ថបទចិន (Input)")
    input_text = st.text_area("ចម្លងអត្ថបទ SRT ដាក់ទីនេះ...", height=400)

with col2:
    st.subheader("📤 លទ្ធផលខ្មែរ (Output)")
    if st.button("🚀 ចាប់ផ្តើមបកប្រែ"):
        if not user_api_key:
            st.error("សូមបញ្ចូល API Key ក្នុង Sidebar ជាមុនសិន!")
        elif not input_text.strip():
            st.warning("សូមបញ្ចូលអត្ថបទដែលត្រូវបកប្រែ!")
        else:
            try:
                with st.spinner("កំពុងបកប្រែ... សូមរង់ចាំ"):
                    translated_output = translate_srt(input_text, user_api_key)
                    st.text_area("លទ្ធផល៖", value=translated_output, height=355)
                    
                    st.download_button(
                        label="ទាញយកឯកសារ .srt",
                        data=translated_output,
                        file_name="translated_khmer.srt",
                        mime="text/plain"
                    )
                    st.success("បកប្រែរួចរាល់!")
            except Exception as e:
                st.error(f"បញ្ហាបច្ចេកទេស៖ {str(e)}")
                st.info("ប្រសិនបើនៅតែឃើញ Error 404 សូមប្រាកដថាអ្នកបាន Update requirements.txt រួចរាល់។")

st.markdown("---")
st.caption("អភិវឌ្ឍន៍ដោយប្រើ Streamlit និង Gemini 1.5 Flash")
