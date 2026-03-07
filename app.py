import streamlit as st
import google.generativeai as genai

# ១. ការកំណត់ទំព័រ Website
st.set_page_config(page_title="SRT Chinese to Khmer Translator", layout="wide")

st.title("🏯 ឧបករណ៍បកប្រែរឿងភាគចិនទៅខ្មែរ")
st.markdown("---")

# ២. ផ្នែក Sidebar
st.sidebar.header("ការកំណត់")
api_key = st.sidebar.text_input("បញ្ចូល Gemini API Key:", type="password")
# ឱ្យអ្នកប្រើជ្រើសរើស Model ដើម្បីការពារ Error
model_choice = st.sidebar.selectbox("ជ្រើសរើសម៉ូដែល AI:", ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"])

st.sidebar.info("យក API Key ពី: [Google AI Studio](https://aistudio.google.com/)")

# ៣. មុខងារបកប្រែ
def translate_srt(text, api_key, model_name):
    genai.configure(api_key=api_key)
    
    # បង្កើតម៉ូដែលតាមការជ្រើសរើស
    model = genai.GenerativeModel(model_name=model_name)
    
    prompt = f"""
    You are a professional movie subtitle translator. 
    Translate the following Chinese SRT content into natural Khmer.
    
    Rules:
    1. Do NOT change the timestamps or subtitle numbers.
    2. Make the Khmer translation sound like a real movie dialogue.
    3. Output ONLY the translated SRT.
    
    Text:
    {text}
    """
    
    response = model.generate_content(prompt)
    return response.text

# ៤. រចនាសម្ព័ន្ធ UI
col1, col2 = st.columns(2)

with col1:
    st.subheader("📥 អត្ថបទចិន (SRT)")
    input_text = st.text_area("ចម្លងអត្ថបទដាក់ទីនេះ...", height=400, key="input")

with col2:
    st.subheader("📤 លទ្ធផលជាភាសាខ្មែរ")
    if st.button("ចាប់ផ្តើមបកប្រែ"):
        if not api_key:
            st.error("សូមបញ្ចូល API Key!")
        elif not input_text.strip():
            st.warning("សូមបញ្ចូលអត្ថបទ!")
        else:
            try:
                with st.spinner(f"កំពុងប្រើ {model_choice} ដើម្បីបកប្រែ..."):
                    result = translate_srt(input_text, api_key, model_choice)
                    st.text_area("លទ្ធផល:", value=result, height=350)
                    
                    st.download_button(
                        label="ទាញយក File .srt",
                        data=result,
                        file_name="translated_khmer.srt",
                        mime="text/plain"
                    )
            except Exception as e:
                st.error(f"កំហុសបច្ចេកទេស៖ {str(e)}")
                st.info("បើសិនជា Error 404 សូមសាកល្បងប្តូរទៅប្រើម៉ូដែល 'gemini-pro' ក្នុង Sidebar។")

st.markdown("---")
st.caption("អភិវឌ្ឍន៍ដោយប្រើ Streamlit និង Gemini API")
