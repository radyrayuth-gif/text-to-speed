import streamlit as st
import google.generativeai as genai

# ១. ការកំណត់ទំព័រ Website
st.set_page_config(page_title="SRT Chinese to Khmer Translator", layout="wide")

st.title("🏯 ឧបករណ៍បកប្រែរឿងភាគចិនទៅខ្មែរ")
st.markdown("---")

# ២. ផ្នែក Sidebar សម្រាប់បញ្ចូល API Key
st.sidebar.header("ការកំណត់")
api_key = st.sidebar.text_input("បញ្ចូល Gemini API Key:", type="password")
st.sidebar.info("អ្នកអាចយក API Key បានពី: [Google AI Studio](https://aistudio.google.com/)")

# ៣. មុខងារចម្បងសម្រាប់ការបកប្រែ
def translate_srt(text, api_key):
    # កំណត់រចនាសម្ព័ន្ធ API
    genai.configure(api_key=api_key)
    
    # ប្រើម៉ូដែល gemini-1.5-flash ដែលមានល្បឿនលឿន និងយល់ Context បានល្អ
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    
    # បង្កើត Prompt ដើម្បីបញ្ជា AI ឲ្យបកប្រែចំគោលដៅ
    prompt = f"""
    You are an expert Chinese-to-Khmer translator specializing in movie subtitles.
    Task: Translate the following SRT content into natural, emotional, and grammatically correct Khmer.
    
    Strict Rules:
    1. Keep all subtitle numbers and timestamps (e.g., 00:00:01,400 --> 00:00:02,740) exactly as they are.
    2. Do not add any introductory text, only provide the translated SRT content.
    3. Translate the meaning naturally for a movie context, not word-for-word.
    
    SRT Content to translate:
    {text}
    """
    
    response = model.generate_content(prompt)
    return response.text

# ៤. រចនាសម្ព័ន្ធផ្ទៃកម្មវិធី (UI)
col1, col2 = st.columns(2)

with col1:
    st.subheader("📥 អត្ថបទចិន (Original)")
    input_text = st.text_area("ចម្លងអត្ថបទ SRT ដាក់ទីនេះ...", height=400)

with col2:
    st.subheader("📤 លទ្ធផលជាភាសាខ្មែរ (Translated)")
    if st.button("ចាប់ផ្តើមបកប្រែឥឡូវនេះ"):
        if not api_key:
            st.error("សូមបញ្ចូល API Key ជាមុនសិន!")
        elif not input_text.strip():
            st.warning("សូមបញ្ចូលអត្ថបទចិនដែលត្រូវបកប្រែ!")
        else:
            try:
                with st.spinner("កំពុងបកប្រែ... សូមរង់ចាំមួយភ្លែត"):
                    translated_result = translate_srt(input_text, api_key)
                    st.text_area("លទ្ធផល:", value=translated_result, height=355)
                    
                    # ប៊ូតុងទាញយកឯកសារ
                    st.download_button(
                        label="ទាញយកឯកសារបកប្រែ (.srt)",
                        data=translated_result,
                        file_name="khmer_subtitle.srt",
                        mime="text/plain"
                    )
                    st.success("ការបកប្រែបានជោគជ័យ!")
            except Exception as e:
                st.error(f"កើតមានបញ្ហា: {str(e)}")

st.markdown("---")
st.caption("អភិវឌ្ឍន៍ដោយប្រើ Streamlit និង Gemini 1.5 Flash API")
