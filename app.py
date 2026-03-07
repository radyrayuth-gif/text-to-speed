import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="SRT Chinese-Khmer Translator")
st.title("🏯 ឧបករណ៍បកប្រែ Subtitle")

# ការកំណត់ API
api_key = st.sidebar.text_input("បញ្ចូល API Key:", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # ប្រើម៉ូដែលដែលស្ថិតក្នុងបញ្ជី Stable
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        input_text = st.text_area("បញ្ចូលអត្ថបទ SRT ចិន:", height=300)
        
        if st.button("🚀 ចាប់ផ្តើមបកប្រែ"):
            prompt = f"Translate the following SRT content from Chinese to Khmer. Keep timestamps.\n\n{input_text}"
            response = model.generate_content(prompt)
            st.text_area("លទ្ធផលខ្មែរ:", value=response.text, height=300)
            
    except Exception as e:
        st.error(f"បញ្ហាកូដ៖ {str(e)}")
        st.info("ប្រសិនបើឃើញ Error 404 ម្តងទៀត សូមពិនិត្យមើលថាអ្នកបាន Update 'requirements.txt' រួចរាល់ហើយឬនៅ។")
