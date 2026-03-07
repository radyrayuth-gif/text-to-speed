import streamlit as st
import google.generativeai as genai
import time
import io

# កំណត់ទំហំបកប្រែម្តងៗ (៥០ blocks ដើម្បីកុំឱ្យលើស Limit)
CHUNK_SIZE = 50

def split_srt_content(text):
    """បំបែកអត្ថបទ SRT ជាផ្នែកៗ"""
    blocks = text.strip().split('\n\n')
    for i in range(0, len(blocks), CHUNK_SIZE):
        yield '\n\n'.join(blocks[i:i + CHUNK_SIZE])

def translate_logic(text_chunk, model):
    """មុខងារផ្ញើទៅ Gemini បកប្រែ"""
    # បន្ថែម Instructions ឱ្យដាច់ដោយឡែកដើម្បីឱ្យ AI ធ្វើការបានល្អ
    prompt = (
        "Translate the following Chinese subtitles into natural Khmer. "
        "Keep the SRT format (numbers and timestamps) exactly as they are. "
        "Only output the translated SRT content.\n\n"
        f"{text_chunk}"
    )
    response = model.generate_content(prompt)
    return response.text

# --- រៀបចំ UI ---
st.set_page_config(page_title="SRT Chinese-Khmer Pro", layout="wide", page_icon="🎬")

st.title("🎬 SRT Chinese-Khmer Pro Translator")
st.markdown("---")

# Sidebar សម្រាប់ API Key
with st.sidebar:
    st.header("⚙️ ការកំណត់")
    api_key = st.text_input("បញ្ចូល Gemini API Key:", type="password")
    st.info("ចំណាំ៖ ប្រសិនបើជួប Error 404 សូមប្រាកដថាអ្នកបានប្រើបណ្ណាល័យជំនាន់ថ្មីក្នុង requirements.txt")

# កន្លែង Upload File
uploaded_file = st.file_uploader("ជ្រើសរើសឯកសារ SRT (ចិន)", type=["srt"])

if uploaded_file is not None:
    # អានឯកសារ
    try:
        content = uploaded_file.getvalue().decode("utf-8")
    except UnicodeDecodeError:
        content = uploaded_file.getvalue().decode("gbk") # សម្រាប់ File ចិនខ្លះដែលប្រើ Encoding ចាស់

    st.success(f"✅ បានរកឃើញឯកសារ៖ {uploaded_file.name}")
    
    if st.button("🚀 ចាប់ផ្តើមបកប្រែ"):
        if not api_key:
            st.error("❌ សូមបញ្ចូល API Key ក្នុង Sidebar!")
        else:
            try:
                # កំណត់ Configuration
                genai.configure(api_key=api_key)
                
                # ប្រើ 'gemini-1.5-flash-latest' ដើម្បីជៀសវាង Error 404
                model = genai.GenerativeModel("gemini-1.5-flash-latest")
                
                chunks = list(split_srt_content(content))
                translated_full = []
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for index, chunk in enumerate(chunks):
                    status_text.text(f"⏳ កំពុងបកប្រែផ្នែកទី {index + 1} នៃ {len(chunks)}...")
                    
                    result = translate_logic(chunk, model)
                    translated_full.append(result)
                    
                    # Update Progress
                    progress_bar.progress((index + 1) / len(chunks))
                    
                    # សម្រាក ១ វិនាទីការពារ Rate Limit
                    time.sleep(1.5)

                final_srt = "\n\n".join(translated_full)
                
                st.divider()
                st.subheader("🎉 ការបកប្រែរួចរាល់!")
                
                # ប៊ូតុងទាញយក
                st.download_button(
                    label="📥 ទាញយកឯកសារបកប្រែ (.srt)",
                    data=final_srt,
                    file_name=f"Khmer_{uploaded_file.name}",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"❌ បញ្ហាបច្ចេកទេស៖ {str(e)}")
                st.warning("ជំនួយ៖ សាកល្បងត្រួតពិនិត្យ API Key ឬប្តូរទៅប្រើ Model 'gemini-pro' ប្រសិនបើ Flash មានបញ្ហា។")

st.markdown("---")
st.caption("អភិវឌ្ឍន៍ដោយប្រើ Streamlit និង Gemini 1.5 Flash API")
