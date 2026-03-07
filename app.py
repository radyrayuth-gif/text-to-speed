import streamlit as st
import google.generativeai as genai
import time

# មុខងារបកប្រែអត្ថបទ SRT
def translate_srt(api_key, content):
    # កំណត់ Configuration របស់ Gemini
    genai.configure(api_key=api_key)
    
    # ប្រើឈ្មោះ Model នេះដើម្បីជៀសវាង Error 404 (ផ្លាស់ប្តូរពី v1beta ទៅ v1)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = (
        "You are a professional subtitle translator. Translate the following Chinese SRT content into natural Khmer. "
        "Strictly keep the exact SRT format, including subtitle numbers and timestamps. "
        "Do not include any extra text or explanations.\n\n"
        f"{content}"
    )
    
    response = model.generate_content(prompt)
    return response.text

# --- ការរៀបចំផ្ទៃកម្មវិធី (User Interface) ---
st.set_page_config(page_title="SRT Pro Translator", layout="wide", page_icon="🎬")

st.title("🎬 SRT Chinese-Khmer Pro Translator")
st.markdown("---")

# ផ្នែកចំហៀងសម្រាប់បញ្ចូល API Key
with st.sidebar:
    st.header("⚙️ ការកំណត់")
    api_key = st.text_input("បញ្ចូល Gemini API Key:", type="password")
    st.divider()
    st.info("💡 ប្រសិនបើជួប Error 404 សូម Delete App រួច Deploy ថ្មីក្នុង Streamlit Dashboard។")

# កន្លែងទាញឯកសារចូល
uploaded_file = st.file_uploader("ជ្រើសរើសឯកសារ SRT (ចិន)", type=["srt"])

if uploaded_file is not None:
    # ព្យាយាមអានឯកសារ (ត្រួតពិនិត្យ Encoding សម្រាប់អក្សរចិន)
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
                with st.spinner("⏳ កំពុងបកប្រែ... សូមរង់ចាំបន្តិច..."):
                    result = translate_srt(api_key, raw_content)
                    st.success("✅ ការបកប្រែត្រូវបានបញ្ចប់ជោគជ័យ!")
                    
                    # ប៊ូតុងសម្រាប់ទាញយកឯកសារ
                    st.download_button(
                        label="📥 ទាញយកឯកសារបកប្រែ (.srt)",
                        data=result,
                        file_name=f"Khmer_{uploaded_file.name}",
                        mime="text/plain"
                    )
                    
                    # បង្ហាញលទ្ធផលខ្លះៗ (Preview)
                    with st.expander("មើលលទ្ធផលបន្តិចបន្តួច"):
                        st.text(result[:1000] + "...")
                        
            except Exception as e:
                st.error(f"❌ បញ្ហាបច្ចេកទេស៖ {str(e)}")
                st.info("ជំនួយ៖ Error 404 នេះមកពីប្រព័ន្ធមិនទាន់ Update បណ្ណាល័យថ្មី។ សូមសាកល្បងលុប App រួច Deploy ថ្មី។")

st.markdown("---")
st.caption("អភិវឌ្ឍន៍ដោយប្រើ Streamlit និង Gemini 1.5 Flash API")
