import streamlit as st
import google.generativeai as genai
from google.generativeai.types import RequestOptions

# កំណត់ទម្រង់ Website
st.set_page_config(page_title="SRT Chinese-Khmer Translator", layout="wide")
st.title("🏯 ឧបករណ៍បកប្រែ Subtitle ចិន-ខ្មែរ")
st.markdown("---")

# ផ្នែក Sidebar
st.sidebar.header("⚙️ ការកំណត់")
api_key = st.sidebar.text_input("បញ្ចូល Gemini API Key:", type="password")

def translate_srt_stable(text, key):
    # កំណត់ Configuration
    genai.configure(api_key=key)
    
    # បង្កើត Model ដោយបង្ខំឱ្យប្រើ API Version 'v1' (Stable) ដើម្បីជៀសវាង Error 404 លើ v1beta
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash"
    )
    
    # បង្កើត Prompt
    prompt = f"""
    Translate the following Chinese SRT content into natural Khmer. 
    Keep timestamps and subtitle numbers exactly as they are.
    
    Content:
    {text}
    """
    
    # បញ្ជូន Request ដោយកំណត់ Options ឱ្យប្រើប្រាស់ API version v1 ជាដាច់ខាត
    response = model.generate_content(
        prompt,
        options=RequestOptions(api_version="v1")
    )
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
                with st.spinner("កំពុងបកប្រែតាមរយៈ Stable API..."):
                    translated_text = translate_srt_stable(input_data, api_key)
                    st.text_area("លទ្ធផល៖", value=translated_text, height=355)
                    st.success("ការបកប្រែបានជោគជ័យ!")
            except Exception as e:
                st.error(f"បញ្ហាបច្ចេកទេស៖ {str(e)}")
                st.info("បើសិនជានៅតែ Error សូមសាកល្បងចុច 'Manage app' ក្នុង Streamlit រួចជ្រើសរើស 'Reboot App'។")

st.markdown("---")
st.caption("អភិវឌ្ឍន៍ដោយប្រើ Streamlit និង Gemini 1.5 Flash Stable API")
