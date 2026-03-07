import streamlit as st
import google.generativeai as genai
import time
import io

# មុខងារបំបែកអត្ថបទជាដុំៗ ដើម្បីកុំឱ្យលើស Limit របស់ AI
def split_srt_content(text, chunk_size=40):
    blocks = text.strip().split('\n\n')
    for i in range(0, len(blocks), chunk_size):
        yield '\n\n'.join(blocks[i:i + chunk_size])

# មុខងារបកប្រែ
def translate_logic(text_chunk, model):
    prompt = (
        "You are a professional subtitle translator. Translate these Chinese subtitles into natural Khmer. "
        "Keep the exact SRT format, including numbers and timestamps. Do not add any extra text or explanations.\n\n"
        f"{text_chunk}"
    )
    response = model.generate_content(prompt)
    return response.text

# --- ការកំណត់ UI ---
st.set_page_config(page_title="SRT Chinese-Khmer Pro", layout="wide", page_icon="🎬")
st.title("🎬 SRT Chinese-Khmer Pro Translator")
st.info("💡 ប្រសិនបើជួប Error 404 សូមប្រាកដថាអ្នកបាន Reboot App បន្ទាប់ពី Update requirements.txt រួច។")

# Sidebar
with st.sidebar:
    st.header("⚙️ ការកំណត់")
    api_key = st.text_input("បញ្ចូល Gemini API Key:", type="password")
    st.markdown("---")
    st.write("ជំនួយ៖ ប្រើ Model Gemini 1.5 Flash សម្រាប់ល្បឿនលឿន។")

# កន្លែង Upload File
uploaded_file = st.file_uploader("ជ្រើសរើសឯកសារ SRT (ចិន)", type=["srt"])

if uploaded_file is not None:
    # អាន File (ត្រួតពិនិត្យ Encoding សម្រាប់អក្សរចិន)
    try:
        content = uploaded_file.getvalue().decode("utf-8")
    except:
        content = uploaded_file.getvalue().decode("gbk")

    st.success(f"📂 បានអានឯកសារ៖ {uploaded_file.name}")
    
    if st.button("🚀 ចាប់ផ្តើមបកប្រែ"):
        if not api_key:
            st.error("❌ សូមបញ្ចូល API Key ក្នុង Sidebar ជាមុនសិន!")
        else:
            try:
                # កំណត់ Configuration របស់ Gemini
                genai.configure(api_key=api_key)
                
                # ប្រើឈ្មោះ Model សាមញ្ញ (នឹងដើរជាមួយ Library ថ្មីក្នុង requirements.txt)
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                chunks = list(split_srt_content(content))
                translated_full = []
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for index, chunk in enumerate(chunks):
                    status_text.text(f"⏳ កំពុងបកប្រែផ្នែកទី {index + 1} នៃ {len(chunks)}...")
                    
                    result = translate_logic(chunk, model)
                    translated_full.append(result)
                    
                    # ធ្វើបច្ចុប្បន្នភាព Progress
                    progress_bar.progress((index + 1) / len(chunks))
                    
                    # សម្រាក ១.៥ វិនាទី ការពារ Rate Limit សម្រាប់ Key Free
                    time.sleep(1.5)

                final_srt = "\n\n".join(translated_full)
                
                st.divider()
                st.subheader("🎉 ការបកប្រែរួចរាល់!")
                
                st.download_button(
                    label="📥 ទាញយកឯកសារបកប្រែ (.srt)",
                    data=final_srt,
                    file_name=f"Khmer_{uploaded_file.name}",
                    mime="text/plain"
                )
                
                with st.expander("មើលលទ្ធផលខ្លះៗ"):
                    st.text(final_srt[:1000])

            except Exception as e:
                st.error(f"❌ បញ្ហា៖ {str(e)}")
                st.info("ជំនួយ៖ សូមចុច Reboot App ក្នុង Streamlit Cloud បើនៅតែឃើញ Error 404។")

st.markdown("---")
st.caption("Developed with Streamlit & Gemini 1.5 Flash")
