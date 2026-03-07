import streamlit as st
import google.generativeai as genai
import time
import io

# ១. មុខងារបំបែកអត្ថបទជាដុំៗ (Chunking) ដើម្បីកុំឱ្យលើស Limit
def split_srt_content(text, chunk_size=40):
    blocks = text.strip().split('\n\n')
    for i in range(0, len(blocks), chunk_size):
        yield '\n\n'.join(blocks[i:i + chunk_size])

# ២. មុខងារបញ្ជា AI ឱ្យបកប្រែ
def translate_logic(text_chunk, model):
    prompt = (
        "You are a professional subtitle translator. Your task is to translate Chinese subtitles into natural Khmer. "
        "Strictly follow these rules:\n"
        "1. Keep all subtitle numbers and timestamps exactly as they are.\n"
        "2. Translate only the Chinese text into smooth and emotional Khmer.\n"
        "3. Do not include any extra explanations or notes.\n\n"
        f"SRT Content:\n{text_chunk}"
    )
    response = model.generate_content(prompt)
    return response.text

# --- រៀបចំផ្ទៃកម្មវិធី (UI) ---
st.set_page_config(page_title="SRT Chinese-Khmer Pro", layout="wide", page_icon="🎬")

st.title("🎬 SRT Chinese-Khmer Pro Translator")
st.markdown("---")

# ផ្នែកចំហៀងសម្រាប់កំណត់ API Key
with st.sidebar:
    st.header("⚙️ ការកំណត់")
    api_key = st.text_input("បញ្ចូល Gemini API Key:", type="password")
    st.divider()
    st.info("💡 ជំនួយ៖ ប្រសិនបើអ្នកប្រើ API Free សូមកុំបកប្រែញាប់ពេក។")

# កន្លែងទាញឯកសារចូល
uploaded_file = st.file_uploader("ជ្រើសរើសឯកសារ SRT (ចិន)", type=["srt"])

if uploaded_file is not None:
    # ព្យាយាមអាន File (ត្រួតពិនិត្យ Encoding សម្រាប់អក្សរចិន)
    try:
        raw_content = uploaded_file.getvalue().decode("utf-8")
    except UnicodeDecodeError:
        raw_content = uploaded_file.getvalue().decode("gbk")

    st.success(f"📂 បានអានឯកសារ៖ {uploaded_file.name}")
    
    if st.button("🚀 ចាប់ផ្តើមបកប្រែឥឡូវនេះ"):
        if not api_key:
            st.error("❌ សូមបញ្ចូល API Key ក្នុង Sidebar ជាមុនសិន!")
        else:
            try:
                # កំណត់ Configuration របស់ Gemini
                genai.configure(api_key=api_key)
                
                # ប្រើម៉ូដែល Gemini 1.5 Flash (Version ថ្មីបំផុត)
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                chunks = list(split_srt_content(raw_content))
                translated_full = []
                
                # បង្ហាញដំណើរការបកប្រែ (Progress)
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for index, chunk in enumerate(chunks):
                    status_text.text(f"⏳ កំពុងបកប្រែផ្នែកទី {index + 1} នៃ {len(chunks)}...")
                    
                    # ហៅការបកប្រែ
                    result = translate_logic(chunk, model)
                    translated_full.append(result)
                    
                    # ធ្វើបច្ចុប្បន្នភាព Progress Bar
                    progress_bar.progress((index + 1) / len(chunks))
                    
                    # សម្រាក ១.៥ វិនាទី ដើម្បីការពារ Rate Limit (សម្រាប់ API Key Free)
                    time.sleep(1.5)

                # ផ្គុំអត្ថបទដែលបកប្រែរួចចូលគ្នាវិញ
                final_srt = "\n\n".join(translated_full)
                
                st.divider()
                st.subheader("🎉 ការបកប្រែត្រូវបានបញ្ចប់!")
                
                # ប៊ូតុងសម្រាប់ Download
                st.download_button(
                    label="📥 ទាញយកឯកសារបកប្រែរួច (.srt)",
                    data=final_srt,
                    file_name=f"Khmer_{uploaded_file.name}",
                    mime="text/plain"
                )
                
                # បង្ហាញ Preview លទ្ធផលខ្លះៗ
                with st.expander("មើលលទ្ធផលបន្តិចបន្តួច (Preview)"):
                    st.text(final_srt[:1500] + "...")

            except Exception as e:
                st.error(f"❌ បញ្ហាបច្ចេកទេស៖ {str(e)}")
                st.info("ជំនួយ៖ ប្រសិនបើចេញ Error 404 សូមប្រាកដថាអ្នកបានចុច 'Reboot App' ក្នុង Streamlit Cloud Dashboard រួចរាល់។")

st.markdown("---")
st.caption("អភិវឌ្ឍន៍ដោយប្រើ Streamlit និង Gemini 1.5 Flash API - បកប្រែបានលឿន និងរក្សាទម្រង់ដើម ១០០%")
