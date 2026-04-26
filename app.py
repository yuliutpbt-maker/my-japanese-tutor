import streamlit as st
import google.generativeai as genai
import time
from streamlit_mic_recorder import mic_recorder

# --- 1. 初始化 ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("models/gemini-3.1-flash-lite-preview")
except:
    st.error("API 設定錯誤")
    st.stop()

st.set_page_config(page_title="日文練習 (最終穩定版)")

# --- 2. 終極語音播放邏輯 ---
def play_audio(text):
    # 使用純 JavaScript Web Speech API
    # 這是最穩定、不需要外部連結、不會被 CORS 擋住的方法
    js_code = f"""
    <script>
    (function() {{
        // 強制停止之前的聲音
        window.speechSynthesis.cancel();
        
        var msg = new SpeechSynthesisUtterance('{text}');
        msg.lang = 'ja-JP';
        msg.rate = 0.85;
        msg.volume = 1.0;

        // 針對手機的特殊喚醒：多點幾次 speak
        window.speechSynthesis.speak(msg);
        
        // 如果瀏覽器沒反應，嘗試在 console 報錯
        msg.onerror = function(event) {{
            console.error('TTS Error: ' + event.error);
        }};
    }})();
    </script>
    """
    st.components.v1.html(js_code, height=0)

st.title("日文練習器")

# --- 3. 測試介面 ---
target = st.text_input("輸入日文：", "こんにちは")

if st.button("🔈 撥放聲音"):
    # 電腦版點擊這個必動
    play_audio(target)

st.divider()

# --- 4. 錄音判定 ---
audio = mic_recorder(start_prompt="🔴 錄音", stop_prompt="⬛ 判定", key="v_final_rec")

if audio:
    with st.spinner("判定中..."):
        try:
            # 傳送錄音數據
            response = model.generate_content([
                f"原文：『{target}』。請判定發音並給分。",
                {"mime_type": "audio/wav", "data": audio['bytes']}
            ])
            st.success("分析結果：")
            st.write(response.text)
        except Exception as e:
            st.error(f"分析失敗：{e}")
