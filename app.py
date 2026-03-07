import streamlit as st
import google.generativeai as genai

# ១. ការកំណត់ទំព័រ និងរូបរាង Website
st.set_page_config(page_title="SRT Chinese-Khmer Translator", layout="wide")
st.title("🏯 ឧបករណ៍បកប្រែ Subtitle ចិន-ខ្មែរ")
st.markdown("---")

# ២. ផ្នែក Sidebar សម្រាប់ការកំណត់
st.sidebar.header("⚙️ ការកំណត់កម្មវិធី")
api_key = st.sidebar.text_input("បញ្ចូល Gemini API Key:", type="password")

# បន្ថែមជម្រើសម៉ូដែលដើម្បីការពារ Error 404
# ប្រសិនបើ gemini-1.5-flash មិនដើរ អ្នកអាចប្តូរទៅ gemini-pro
model_choice = st.sidebar.selectbox(
    "ជ្រើសរើសម៉ូដែល AI:", 
    ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
)

st.sidebar.info("ជំនួយ៖ ប្រសិនបើជួប Error 404 សូមសាកល្បងប្តូរទៅប្រើ 'gemini-pro'។")

# ៣. មុខងារបកប្រែដែលរក្សាទម្រង់ SRT
def translate_srt_logic(text, key, model_name):
    # កំណត់ Configuration ឱ្យ API
    genai.configure(api_key=key)
    
    # បង្កើតម៉ូដែលតាមជម្រើសរបស់អ្នកប្រើ
    model = genai.GenerativeModel(model_name=model_name)
    
    # Prompt ដែលរៀបចំឡើងដើម្បីឱ្យបកប្រែបានត្រឹមត្រូវដូច Google Gemini ផ្ទាល់
    prompt = f"""
    You are a professional subtitle translator. Your task is to translate Chinese SRT subtitles into Khmer.
    
    Strict Instructions:
    1. Keep all subtitle numbers and timestamps (e.g., 00:00:01,400 --> 00:00:02,740) exactly as they are.
    2. Translate the Chinese text into natural, emotional, and contextually correct Khmer for movies.
    3. Do not include any explanations or extra text. Output only the SRT format.
    
    SRT Content:
    {text}
    """
    
    response = model.generate_content(prompt)
    return response.text

# ៤. រចនាសម្ព័ន្ធផ្ទៃកម្មវិធី (UI)
col1, col2 = st.columns(2)

with col1:
    st.subheader("📥 អត្ថបទចិន (Input)")
    input_data = st.text_area("ចម្លងអត្ថបទ SRT របស់អ្នកដាក់ទីនេះ...", height=400)

with col2:
    st.subheader("📤 លទ្ធផលខ្មែរ (Output)")
    if st.button("🚀 ចាប់ផ្តើមបកប្រែ"):
        if not api_key:
            st.error("សូមបញ្ចូល API Key របស់អ្នកនៅក្នុង Sidebar!")
        elif not input_data.strip():
            st.warning("សូមបញ្ចូលអត្ថបទដែលត្រូវបកប្រែ!")
        else:
            try:
                with st.spinner(f"កំពុងបកប្រែដោយប្រើ {model_choice}..."):
                    # ហៅមុខងារបកប្រែ
                    translated_text = translate_srt_logic(input_data, api_key, model_choice)
                    st.text_area("លទ្ធផលបកប្រែ៖", value=translated_text, height=350)
                    
                    # ប៊ូតុងទាញយក File
                    st.download_button(
                        label="ទាញយកឯកសារ .srt",
                        data=translated_text,
                        file_name="khmer_sub.srt",
                        mime="text/plain"
                    )
                    st.success("ការបកប្រែបានជោគជ័យ!")
            except Exception as e:
                # បង្ហាញ Error ឱ្យបានច្បាស់លាស់
                st.error(f"មានបញ្ហាកើតឡើង៖ {str(e)}")

st.markdown("---")
st.caption("អភិវឌ្ឍន៍ដោយប្រើ Streamlit និង Gemini API")
