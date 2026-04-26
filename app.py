import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder

# 1. 核心初始化 (使用 1.5 Flash 追求最高穩定度)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-flash")
except:
    st.error("API 設定錯誤")
    st.stop()

# 2. 萬用語音播放 (不使用外部連結，避免 CORS 錯誤)
def play_audio(text):
    js_code = f"""
    <script>
        window.speechSynthesis.cancel();
        var m = new SpeechSynthesisUtterance('{text}');
        m.lang = 'ja-JP';
        window.speechSynthesis.speak(m);
    </script>
    """
    st.components.v1.html(js_code, height=0)

st.title("日文練習 (穩定版)")

# 3. 簡單路徑處理
if 'sentence' not in st.session_state:
    st.session_state.sentence = "こんにちは、元気ですか？"

target_text = st.text_input("要練習的句子：", st.session_state.sentence)

if st.button("🔈 聽發音"):
    play_audio(target_text)

st.divider()

# 4. 錄音與分析 (極簡結構，減少數據封裝層級)
audio = mic_recorder(start_prompt="🔴 錄音", stop_prompt="⬛ 判定", key="simple_rec")

if audio:
    with st.spinner("分析中..."):
        try:
            # 這是最簡單、最不容易當機的數據格式
            content = [
                f"請分析這段錄音是否符合原文：『{target_text}』。請給評分與建議。",
                {"mime_type": "audio/wav", "data": audio['bytes']}
            ]
            response = model.generate_content(content)
            st.success("分析結果：")
            st.write(response.text)
        except Exception as e:
            st.error(f"分析當機，原因：{e}")
