import streamlit as st
import google.generativeai as genai
import json
import os
import urllib.parse
from streamlit_mic_recorder import mic_recorder

# --- 1. 初始化 ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("models/gemini-3.1-flash-lite-preview")
except Exception as e:
    st.error(f"API 設定錯誤: {e}")
    st.stop()

st.set_page_config(page_title="I Japanese 練習器", layout="wide")

# --- 2. 核心語音播放 (改用 Google TTS 接口，手機最穩定) ---
def play_audio(text):
    # 將文字轉為 URL 編碼
    query = urllib.parse.quote(text)
    # 使用 Google 翻譯的語音接口（這在手機上被視為多媒體音，不會被靜音鍵鎖死）
    tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={query}&tl=ja&client=tw-ob"
    
    # 使用 HTML5 audio 標籤並設定自動播放
    audio_html = f"""
        <audio autoplay name="media">
            <source src="{tts_url}" type="audio/mpeg">
        </audio>
    """
    st.components.v1.html(audio_html, height=0)

# --- 3. 讀取教材 ---
save_path = "Japanese_Lessons"
if not os.path.exists(save_path):
    st.error("教材資料夾遺失")
else:
    files = [f for f in os.listdir(save_path) if f.endswith('.json')]
    selected_file = st.selectbox("🎯 選擇課目", files)
    with open(os.path.join(save_path, selected_file), 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    sentences = data['sentences']
    if 'current_idx' not in st.session_state:
        st.session_state.current_idx = 0
    
    idx = st.session_state.current_idx
    current_s = sentences[idx]

    # --- 4. 介面介面 ---
    st.subheader("📖 全文預覽")
    for i, s in enumerate(sentences):
        if st.button(s, key=f"btn_{i}", type="primary" if i==idx else "secondary"):
            st.session_state.current_idx = i
            play_audio(s) # 點擊後直接觸發 HTML5 播放
            st.rerun()

    st.divider()
    st.info(f"當前句子：{current_s}")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔈 聽範例音"):
            play_audio(current_s)
    with c2:
        if st.button("⏭️ 下一句"):
            st.session_state.current_idx = (idx + 1) % len(sentences)
            st.rerun()

    # --- 5. 錄音判定 ---
    st.write("---")
    audio_record = mic_recorder(
        start_prompt="🔴 開始錄音",
        stop_prompt="⬛ 結束並判定",
        key=f"rec_final_{idx}"
    )

    if audio_record:
        with st.spinner("Gemini 正在分析您的聲音..."):
            try:
                audio_input = {"mime_type": "audio/wav", "data": audio_record['bytes']}
                prompt = f"原文：'{current_s}'。請聽我的發音，評分並給建議。格式：SCORE: 0-100 / ADVICE: 日語建議"
                response = model.generate_content([prompt, audio_input])
                st.markdown("##### 📊 判定結果")
                st.write(response.text)
                if "SCORE" in response.text:
                    st.balloons()
            except Exception as e:
                st.error(f"判定失敗：{e}")
