import streamlit as st
from openai import OpenAI
st.set_page_config(page_title="KhmerTranslate AI Pro", page_icon="🎬", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .main-title { color: #1e3a8a; text-align: center; font-size: 30px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)
st.markdown('<div class="main-title">AI Subtitle Translator (Cinematic)</div>', unsafe_allow_html=True)
with st.sidebar:
    st.title("ការកំណត់")
    api_key = st.text_input("OpenAI API Key", type="password")
    # បន្ថែមជម្រើសរចនាបថនៃការនិយាយ
    genre = st.selectbox("ជ្រើសរើសប្រភេទរឿង:", ["រឿងភាគសម័យ (Modern)", "រឿងបុរាណ/ក្បាច់គុន (Wuxia)", "រឿងមនោសញ្ចេតនា (Romance)"])
uploaded_file = st.file_uploader("Upload Chinese SRT File", type="srt")
def ai_translate_srt(content, api_key, genre):
    client = OpenAI(api_key=api_key)
    
    # ការណែនាំ AI ឱ្យបកប្រែតាមបែប "មនុស្សនិយាយ" មិនមែន "ម៉ាស៊ីនបក"
    prompt_context = f"ប្រភេទរឿង៖ {genre}"
    
    system_instruction = f"""
    You are a professional movie dubbing scriptwriter and Khmer translator. 
    Your goal is to translate Chinese subtitles into Khmer that sounds like real people talking in a movie ({genre}).
    
    RULES:
    1. DO NOT translate word-for-word. Use Khmer idioms and natural speaking patterns.
    2. Adjust pronouns based on {genre}. (e.g., in Wuxia use 'ទូលបង្គំ', 'ទ្រង់', 'បងធំ', 'និកាយ').
    3. Keep the SRT format (numbers and timecodes) EXACTLY the same.
    4. Ensure correct Khmer spelling and grammar.
    5. If a sentence is an exclamation or emotion, translate it with the right feeling.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o", # ប្រើ GPT-4o ខ្លាំងជាង mini សម្រាប់ការបកប្រែសាច់រឿង
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Context: {prompt_context}\n\nContent to translate:\n{content}"}
            ],
            temperature=0.4 
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"
if uploaded_file is not None:
    if st.button("Start AI Translation", type="primary", use_container_width=True):
        if not api_key:
            st.warning("សូមបញ្ចូល API Key!")
        else:
            with st.spinner('AI កំពុងរៀបរៀងឃ្លាប្រយោគឱ្យដូចសាច់រឿងពិតៗ...'):
                raw_text = uploaded_file.read().decode("utf-8")
                translated_result = ai_translate_srt(raw_text, api_key, genre)
                
                if "Error:" in translated_result:
                    st.error(translated_result)
                else:
                    st.success("បកប្រែរួចរាល់តាមបែបធម្មជាតិ!")
                    st.download_button("Download Cinematic SRT", translated_result, file_name=f"Cinema_{uploaded_file.name}")
