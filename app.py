import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder

# --- 1. 初始化 (只用你確定能動的模型名稱) ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # 回歸你電腦測試成功過的唯一版本
    model = genai.GenerativeModel("models/gemini-3.1-flash-lite-preview")
except Exception as e:
    st.error(f"設定錯誤: {e}")
    st.stop()

st.title("日文口說測試 (基準版)")

# --- 2. 語音播放 (使用最簡單的 JS，電腦版必動) ---
def play_audio(text):
    js = f"""
    <script>
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance('{text}');
        msg.lang = 'ja-JP';
        window.speechSynthesis.speak(msg);
    </script>
    """
    st.components.v1.html(js, height=0)

# --- 3. 測試介面 ---
target = st.text_input("輸入日文測試：", "こんにちは")

if st.button("🔈 聽發音"):
    play_audio(target)

st.divider()

# --- 4. 判定功能 (最簡化的封裝) ---
st.write("錄音並按結束進行判定：")
audio = mic_recorder(start_prompt="🔴 錄音", stop_prompt="⬛ 結束", key="test_rec")

if audio:
    with st.spinner("Gemini 分析中..."):
        try:
            # 這是最不容易出錯的傳輸方式
            response = model.generate_content([
                f"原文：『{target}』。請判定發音並給分。",
                {"mime_type": "audio/wav", "data": audio['bytes']}
            ])
            st.success("結果回傳：")
            st.write(response.text)
        except Exception as e:
            st.error(f"分析失敗，錯誤碼：{e}")
