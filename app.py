import streamlit as st
import google.generativeai as genai
import base64
from streamlit_mic_recorder import mic_recorder

# --- 1. 初始化 ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("models/gemini-3.1-flash-lite-preview")
except:
    st.error("API 設定錯誤")
    st.stop()

st.title("日文練習 (多媒體強制播放版)")

# --- 2. 核心技術：Google TTS 接口 (模擬音樂播放) ---
def play_audio(text):
    # 使用 Google TTS 接口，這會產生一個真正的音訊連結
    tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={text}&tl=ja&client=tw-ob"
    
    # 用 HTML5 <audio> 標籤，這跟 YouTube 的播放等級一樣
    audio_html = f"""
        <audio autoplay>
            <source src="{tts_url}" type="audio/mpeg">
        </audio>
    """
    st.components.v1.html(audio_html, height=0)

# --- 3. 測試介面 ---
target = st.text_input("輸入日文：", "こんにちは")

if st.button("🔈 強制發聲 (YouTube 等級)"):
    play_audio(target)

st.divider()

# --- 4. 判定功能 ---
audio = mic_recorder(start_prompt="🔴 錄音", stop_prompt="⬛ 判定", key="final_rec")

if audio:
    with st.spinner("判定中..."):
        try:
            response = model.generate_content([
                f"原文：『{target}』。請評分發音。",
                {"mime_type": "audio/wav", "data": audio['bytes']}
            ])
            st.write(response.text)
        except Exception as e:
            st.error(f"分析失敗：{e}")
