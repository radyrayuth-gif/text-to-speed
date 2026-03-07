import streamlit as st
import google.generativeai as genai
import time
import io

# ១. មុខងារបំបែកអត្ថបទជាដុំៗ (Chunking) ដើម្បីកុំឱ្យលើស Limit របស់ AI
def split_srt_content(text, chunk_size=40):
    blocks = text.strip().split('\n\n')
    for i in range(0, len(blocks), chunk_size):
        yield '\n\n'.join(blocks[i:i + chunk_size])

# ២. មុខងារបកប្រែ
def translate_logic(text_chunk, model):
    prompt = (
        "You are a professional subtitle translator. Translate these Chinese subtitles into natural Khmer. "
        "Keep the exact SRT format, including numbers and timestamps. Do not add any extra text.\n\n"
        f"SRT Content:\n{text_chunk}"
    )
    response = model.generate_content(prompt)
    return response.text

# --- រៀបចំផ្ទៃកម្មវិធី (UI) ---
st.set_page_config(page_title="SRT Pro Translator", layout="wide", page_icon="🎬")

st.title("🎬 SRT Chinese-Khmer Pro Translator")
st.markdown("---")

# Sidebar សម្រាប់ API Key
with st.sidebar:
    st.header("⚙️ ការកំណត់")
    api_key = st.text_input("បញ្ចូល Gemini API Key:", type="password")
    st.divider()
    st.info("💡 ប្រសិនបើជួប Error 404 សូមប្រាកដថាអ្នកបាន Delete App រួច Deploy ថ្មីក្នុង Streamlit Dashboard។")

# កន្លែងទាញឯកសារចូល
uploaded_file = st.file_uploader("ជ្រើសរើសឯកសារ SRT (ចិន)", type=["srt"])

if uploaded_file is not None:
    # ព្យាយាមអាន File (ត្រួតពិនិត្យ Encoding សម្រាប់អក្សរចិន)
    try:
        content = uploaded_file.getvalue().decode("utf-8")
    except:
        content = uploaded_file.getvalue().decode("gbk")

    st.success(f"📂 បានរកឃើញឯកសារ៖ {uploaded_file.name}")
    
    if st.button("🚀 ចាប់ផ្តើមបកប្រែ"):
        if not api_key:
            st.error("❌ សូមបញ្ចូល API Key ក្នុង Sidebar!")
        else:
            try:
                # កំណត់ Configuration របស់ Gemini
                genai.configure(api_key=api_key)
                
                # ប្រើម៉ូដែល Gemini 1.5 Flash (Version ថ្មីបំផុតដែលដើរជាមួយ Library 0.8.3)
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                chunks = list(split_srt_content(content))
                translated_full = []
                
                # បង្ហាញដំណើរការបកប្រែ
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for index, chunk in enumerate(chunks):
                    status_text.text(f"⏳ កំពុងបកប្រែផ្នែកទី {index + 1} នៃ {len(chunks)}...")
                    
                    result = translate_logic(chunk, model)
                    translated_full.append(result)
                    
                    # Update Progress
                    progress_bar.progress((index + 1) / len(chunks))
                    
                    # សម្រាក ១.៥ វិនាទី ការពារ Rate Limit សម្រាប់ API Free
                    time.sleep(1.5)

                final_srt = "\n\n".join(translated_full)
                
                st.divider()
                st.subheader("✅ បកប្រែជោគជ័យ!")
                
                # ប៊ូតុងទាញយក
                st.download_button(
                    label="📥 ទាញយកឯកសារបកប្រែរួច (.srt)",
                    data=final_srt,
                    file_name=f"Khmer_{uploaded_file.name}",
                    mime="text/plain"
                )
                
                with st.expander("មើលលទ្ធផលខ្លះៗ (Preview)"):
                    st.text(final_srt[:1000] + "...")

            except Exception as e:
                st.error(f"❌ បញ្ហា៖ {str(e)}")
                st.info("ជំនួយ៖ Error 404 បញ្ជាក់ថាប្រព័ន្ធមិនទាន់ Update បណ្ណាល័យថ្មី។ សូមសាកល្បង Delete App រួច Deploy ថ្មី។")

st.markdown("---")
st.caption("Developed by Gemini AI Enthusiast")
