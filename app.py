import streamlit as st
import google.generativeai as genai
import time

# មុខងារបកប្រែ SRT
def translate_srt(api_key, content):
    # កំណត់ Configuration របស់ Gemini
    genai.configure(api_key=api_key)
    
    # ប្រើឈ្មោះ Model នេះដើម្បីជៀសវាង Error 404 v1beta
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = (
        "You are a professional translator. Translate the following Chinese SRT content into natural Khmer. "
        "Keep the exact SRT format including timestamps and numbers. "
        "Do not add any explanations.\n\n"
        f"{content}"
    )
    
    response = model.generate_content(prompt)
    return response.text

# --- ការរៀបចំ UI ---
st.set_page_config(page_title="SRT Pro Translator", layout="wide")
st.title("🎬 SRT Chinese-Khmer Pro Translator")

with st.sidebar:
    st.header("⚙️ ការកំណត់")
    api_key = st.text_input("បញ្ចូល Gemini API Key:", type="password")
    st.warning("ប្រសិនបើឃើញ Error 404 សូម Delete App រួច Deploy ថ្មីក្នុង Streamlit Dashboard។")

uploaded_file = st.file_uploader("ជ្រើសរើសឯកសារ SRT (ចិន)", type=["srt"])

if uploaded_file is not None:
    # អានឯកសារ (ត្រួតពិនិត្យ Encoding សម្រាប់អក្សរចិន)
    try:
        raw_content = uploaded_file.getvalue().decode("utf-8")
    except UnicodeDecodeError:
        raw_content = uploaded_file.getvalue().decode("gbk")

    st.success(f"📂 បានរកឃើញឯកសារ៖ {uploaded_file.name}")
    
    if st.button("🚀 ចាប់ផ្តើមបកប្រែ"):
        if not api_key:
            st.error("❌ សូមបញ្ចូល API Key ក្នុង Sidebar ជាមុនសិន!")
        else:
            try:
                with st.spinner("កំពុងបកប្រែ... សូមរង់ចាំ..."):
                    result = translate_srt(api_key, raw_content)
                    st.success("✅ ការបកប្រែត្រូវបានបញ្ចប់!")
                    
                    # ប៊ូតុង Download
                    st.download_button(
                        label="📥 ទាញយកឯកសារបកប្រែ (.srt)",
                        data=result,
                        file_name=f"Khmer_{uploaded_file.name}",
                        mime="text/plain"
                    )
            except Exception as e:
                st.error(f"❌ បញ្ហា៖ {str(e)}")
