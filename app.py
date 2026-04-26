import streamlit as st
import google.generativeai as genai
import time
from streamlit_mic_recorder import mic_recorder

# --- 1. API 初始化 ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("models/gemini-3.1-flash-lite-preview")
except:
    st.error("API 設定錯誤")
    st.stop()

st.set_page_config(page_title="日文練習 (手機音效修復)")

# --- 2. 終極發聲腳本 ---
def play_audio(text):
    # 這是目前對手機最友善的寫法：先 Cancel 再 Speak，並包裝在一個函數中
    js_code = f"""
    <script>
    (function() {{
        window.speechSynthesis.cancel(); 
        var msg = new SpeechSynthesisUtterance('{text}');
        msg.lang = 'ja-JP';
        msg.rate = 0.9;
        
        // 針對手機：必須由使用者點擊後觸發，且有時需要重複呼叫
        window.speechSynthesis.speak(msg);
    }})();
    </script>
    """
    st.components.v1.html(js_code, height=0)

st.title("日文口說練習")

# --- 3. 測試介面 ---
target = st.text_input("輸入日文：", "こんにちは")

# 手機版重點：請點擊這個按鈕來聽聲音
if st.button("🔈 撥放聲音 (手機請點此)"):
    play_audio(target)

st.divider()

# --- 4. 錄音判定 ---
audio = mic_recorder(
    start_prompt="🔴 錄音", 
    stop_prompt="⬛ 判定", 
    key="mobile_fix_rec"
)

if audio:
    with st.spinner("判定中..."):
        try:
            response = model.generate_content([
                f"原文：『{target}』。請判定發音並給分。",
                {"mime_type": "audio/wav", "data": audio['bytes']}
            ])
            st.success("結果回傳：")
            st.write(response.text)
        except Exception as e:
            st.error(f"分析失敗：{e}")
