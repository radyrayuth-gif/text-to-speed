import streamlit as st
import google.generativeai as genai

# កំណត់រូបរាង Website
st.set_page_config(page_title="SRT Chinese-Khmer Translator", layout="wide")
st.title("🏯 ឧបករណ៍បកប្រែ Subtitle ចិន-ខ្មែរ")
st.markdown("---")

# ផ្នែក Sidebar សម្រាប់បញ្ចូល API Key
st.sidebar.header("⚙️ ការកំណត់")
api_key = st.sidebar.text_input("បញ្ចូល Gemini API Key:", type="password")

# មុខងារបកប្រែ
def translate_srt(text, key):
    # កំណត់ការប្រើប្រាស់ API
    genai.configure(api_key=key)
    
    # ហៅប្រើម៉ូដែល Gemini 1.5 Flash
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = f"""
    Translate the following Chinese SRT content into natural Khmer. 
    Keep timestamps and subtitle numbers exactly as they are.
    
    Content:
    {text}
    """
    
    response = model.generate_content(prompt)
    return response.text

# ផ្ទៃកម្មវិធី
col1, col2 = st.columns(2)

with col1:
    st.subheader("📥 អត្ថបទចិន (Input)")
    input_data = st.text_area("ចម្លងអត្ថបទ SRT ដាក់ទីនេះ...", height=400)

with col2:
    st.subheader("📤 លទ្ធផលខ្មែរ (Output)")
    if st.button("🚀 ចាប់ផ្តើមបកប្រែ"):
        if not api_key:
            st.error("សូមបញ្ចូល API Key ក្នុង Sidebar!")
        elif not input_data.strip():
            st.warning("សូមបញ្ចូលអត្ថបទ!")
        else:
            try:
                with st.spinner("កំពុងបកប្រែ..."):
                    translated_text = translate_srt(input_data, api_key)
                    st.text_area("លទ្ធផល៖", value=translated_text, height=355)
                    st.success("ការបកប្រែបានជោគជ័យ!")
            except Exception as e:
                st.error(f"បញ្ហាបច្ចេកទេស៖ {str(e)}")
                st.info("ប្រសិនបើឃើញ Error 404 សូមប្រាកដថាអ្នកបាន Update requirements.txt រួចរាល់។")

st.markdown("---")
st.caption("អភិវឌ្ឍន៍ដោយប្រើ Streamlit និង Gemini 1.5 Flash")
