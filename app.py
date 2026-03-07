import streamlit as st
import google.generativeai as genai
import time
import io

# កំណត់ទំហំបកប្រែម្តងៗ (៥០ ចំណុច Subtitle ក្នុងមួយដង)
CHUNK_SIZE = 50

def split_srt_content(text):
    """បំបែកអត្ថបទ SRT ជាប្លុកៗតាមចំណុចលេខរៀង"""
    blocks = text.strip().split('\n\n')
    for i in range(0, len(blocks), CHUNK_SIZE):
        yield '\n\n'.join(blocks[i:i + CHUNK_SIZE])

def translate_logic(text_chunk, model):
    """មុខងារផ្ញើទៅ Gemini ដើម្បីបកប្រែ"""
    prompt = f"Translate this Chinese SRT content into natural Khmer. Keep timestamps and numbering exactly the same:\n\n{text_chunk}"
    response = model.generate_content(prompt)
    return response.text

# --- រៀបចំផ្ទៃកម្មវិធី (UI) ---
st.set_page_config(page_title="SRT Pro Translator", layout="wide", page_icon="🎬")

st.title("🎬 SRT Chinese-Khmer Pro Translator")
st.info("💡 របៀបប្រើ៖ បញ្ចូល API Key -> Upload ឯកសារ .srt -> ចុចបកប្រែ -> Download លទ្ធផល")

# Sidebar
with st.sidebar:
    st.header("⚙️ ការកំណត់")
    api_key = st.text_input("Gemini API Key:", type="password")
    st.markdown("---")
    st.write("ជំនួយ៖ ម៉ូដែល Flash 1.5 គឺលឿន និងស័ក្តិសមបំផុតសម្រាប់ Subtitle។")

# កន្លែង Upload File
uploaded_file = st.file_uploader("ជ្រើសរើសឯកសារ SRT (ចិន)", type=["srt"])

if uploaded_file is not None:
    # អានឯកសារដែលបាន Upload
    stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
    srt_content = stringio.read()
    
    st.success(f"បានរកឃើញឯកសារ៖ {uploaded_file.name}")
    
    if st.button("🚀 ចាប់ផ្តើមបកប្រែឥឡូវនេះ"):
        if not api_key:
            st.error("សូមបញ្ចូល API Key ក្នុង Sidebar ជាមុនសិន!")
        else:
            try:
                # កំណត់ Configuration របស់ Gemini
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                # បំបែកជាដុំៗ
                chunks = list(split_srt_content(srt_content))
                translated_full = []
                
                # បង្ហាញ Progress
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for index, chunk in enumerate(chunks):
                    status_text.text(f"កំពុងបកប្រែផ្នែកទី {index + 1} នៃ {len(chunks)}...")
                    
                    # ហៅមុខងារបកប្រែ
                    translated_chunk = translate_logic(chunk, model)
                    translated_full.append(translated_chunk)
                    
                    # បច្ចុប្បន្នភាព Progress Bar
                    progress_bar.progress((index + 1) / len(chunks))
                    
                    # ការពារ Rate Limit សម្រាប់ Free API (ឈប់ ១ វិនាទី)
                    time.sleep(1)

                # ផ្គុំលទ្ធផលមកវិញ
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
                
                with st.expander("មើលលទ្ធផលបន្តិចបន្តួច"):
                    st.text(final_srt[:1000] + "...")

            except Exception as e:
                st.error(f"មានបញ្ហាកើតឡើង៖ {str(e)}")

st.markdown("---")
st.caption("Powered by Streamlit & Gemini 1.5 Flash")
