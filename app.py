import streamlit as st
import google.generativeai as genai
import time
import io

# កំណត់ចំនួនការបកប្រែម្តងៗ ដើម្បីកុំឱ្យ AI ហត់ពេក
CHUNK_SIZE = 40 

def split_srt_content(text):
    """បំបែកអត្ថបទ SRT ជាដុំៗតាមរយៈលេខរៀង Subtitle"""
    blocks = text.strip().split('\n\n')
    for i in range(0, len(blocks), CHUNK_SIZE):
        yield '\n\n'.join(blocks[i:i + CHUNK_SIZE])

def translate_logic(text_chunk, model):
    """បញ្ជូនទៅ Gemini ឱ្យបកប្រែ"""
    prompt = (
        "You are a professional subtitle translator. Translate these Chinese subtitles into natural Khmer. "
        "Keep the exact SRT format, including numbers and timestamps. Do not add any extra text. "
        "SRT Content:\n\n" + text_chunk
    )
    # ប្រើ try-except តូចមួយនៅទីនេះដើម្បីការពារបញ្ហា Network
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error translating chunk: {str(e)}"

# --- ការកំណត់ផ្ទៃកម្មវិធី ---
st.set_page_config(page_title="SRT Chinese-Khmer Pro", layout="wide", page_icon="🎬")

st.title("🎬 SRT Chinese-Khmer Pro Translator")
st.markdown("---")

# ផ្នែកចំហៀងសម្រាប់បញ្ចូល API Key
with st.sidebar:
    st.header("⚙️ ការកំណត់")
    api_key = st.text_input("បញ្ចូល Gemini API Key:", type="password")
    st.warning("⚠️ ប្រយ័ត្ន៖ កុំបង្ហាញ API Key របស់អ្នកឱ្យអ្នកដទៃឃើញ។")

# កន្លែងទាញឯកសារចូល
uploaded_file = st.file_uploader("ជ្រើសរើសឯកសារ SRT (ចិន)", type=["srt"])

if uploaded_file is not None:
    # ព្យាយាមអាន File ជា UTF-8 បើមិនចេញទេ ប្រើ GBK (សម្រាប់ File ចិន)
    try:
        raw_content = uploaded_file.getvalue().decode("utf-8")
    except UnicodeDecodeError:
        raw_content = uploaded_file.getvalue().decode("gbk")

    st.success(f"📂 បានអានឯកសារ៖ {uploaded_file.name}")
    
    if st.button("🚀 ចាប់ផ្តើមបកប្រែឥឡូវនេះ"):
        if not api_key:
            st.error("❌ សូមបញ្ចូល API Key ជាមុនសិន!")
        else:
            try:
                # កំណត់ Configuration ថ្មីបំផុត
                genai.configure(api_key=api_key)
                
                # ប្រើឈ្មោះ Model ពេញលេញដើម្បីជៀសវាង Error 404
                model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")
                
                chunks = list(split_srt_content(raw_content))
                translated_full = []
                
                # បង្ហាញដំណើរការ
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for index, chunk in enumerate(chunks):
                    status_text.text(f"⏳ កំពុងបកប្រែផ្នែកទី {index + 1} នៃ {len(chunks)}...")
                    
                    # ហៅការបកប្រែ
                    result = translate_logic(chunk, model)
                    translated_full.append(result)
                    
                    # ធ្វើបច្ចុប្បន្នភាព Progress
                    progress_bar.progress((index + 1) / len(chunks))
                    
                    # សម្រាក ១.៥ វិនាទី ដើម្បីការពារ Rate Limit (សម្រាប់ Key Free)
                    time.sleep(1.5)

                final_srt = "\n\n".join(translated_full)
                
                st.divider()
                st.subheader("✅ បកប្រែជោគជ័យ!")
                
                # ប៊ូតុង Download
                st.download_button(
                    label="📥 ទាញយកឯកសារបកប្រែ (.srt)",
                    data=final_srt,
                    file_name=f"Khmer_{uploaded_file.name}",
                    mime="text/plain"
                )
                
                # បង្ហាញលទ្ធផលខ្លះៗ
                with st.expander("មើលលទ្ធផលបន្តិចបន្តួច"):
                    st.text(final_srt[:1000])

            except Exception as e:
                st.error(f"❌ បញ្ហា៖ {str(e)}")

st.markdown("---")
st.caption("បកប្រែដោយប្រើ Gemini 1.5 Flash - រក្សាលំនាំដើម SRT ១០០%")
