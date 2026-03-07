import streamlit as st
import google.generativeai as genai
import time
import io

# មុខងារបំបែកអត្ថបទជាដុំៗ ដើម្បីកាត់បន្ថយបន្ទុក AI
def split_srt_content(text, chunk_size=40):
    blocks = text.strip().split('\n\n')
    for i in range(0, len(blocks), chunk_size):
        yield '\n\n'.join(blocks[i:i + chunk_size])

def translate_logic(text_chunk, model):
    prompt = (
        "Translate these Chinese subtitles into natural Khmer. "
        "Keep the exact SRT format (numbers and timestamps). "
        "Output ONLY the translated SRT content.\n\n"
        f"{text_chunk}"
    )
    response = model.generate_content(prompt)
    return response.text

# --- ការកំណត់ UI ---
st.set_page_config(page_title="SRT Chinese-Khmer Pro", layout="wide")
st.title("🎬 SRT Chinese-Khmer Pro Translator")

with st.sidebar:
    st.header("⚙️ ការកំណត់")
    api_key = st.text_input("បញ្ចូល Gemini API Key:", type="password")
    st.info("បន្ទាប់ពី Update requirements.txt ហើយ សូមកុំភ្លេច Reboot App ក្នុង Manage App។")

uploaded_file = st.file_uploader("ជ្រើសរើសឯកសារ SRT (ចិន)", type=["srt"])

if uploaded_file is not None:
    # ព្យាយាមអាន File (ត្រួតពិនិត្យ Encoding សម្រាប់អក្សរចិន)
    try:
        content = uploaded_file.getvalue().decode("utf-8")
    except:
        content = uploaded_file.getvalue().decode("gbk")

    st.success(f"📂 បានអានឯកសារ៖ {uploaded_file.name}")
    
    if st.button("🚀 ចាប់ផ្តើមបកប្រែ"):
        if not api_key:
            st.error("❌ សូមបញ្ចូល API Key!")
        else:
            try:
                genai.configure(api_key=api_key)
                
                # ប្រើឈ្មោះ Model ដែលត្រឹមត្រូវសម្រាប់ API v1
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                chunks = list(split_srt_content(content))
                translated_full = []
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for index, chunk in enumerate(chunks):
                    status_text.text(f"⏳ កំពុងបកប្រែផ្នែកទី {index + 1} នៃ {len(chunks)}...")
                    result = translate_logic(chunk, model)
                    translated_full.append(result)
                    progress_bar.progress((index + 1) / len(chunks))
                    time.sleep(1.5) # ការពារ Rate Limit

                final_srt = "\n\n".join(translated_full)
                st.subheader("🎉 ការបកប្រែរួចរាល់!")
                st.download_button("📥 ទាញយកឯកសារ (.srt)", final_srt, file_name=f"KH_{uploaded_file.name}")
                
            except Exception as e:
                st.error(f"❌ បញ្ហា៖ {str(e)}")
                st.info("ប្រសិនបើឃើញ Error 404 សូមប្រាកដថាអ្នកបានចុច Reboot App ក្នុង Streamlit Cloud Dashboard។")
