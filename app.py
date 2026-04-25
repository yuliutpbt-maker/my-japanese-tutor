import streamlit as st
import google.generativeai as genai
import json
import os
from streamlit_mic_recorder import mic_recorder

# --- API 初始化 ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("models/gemini-3.1-flash-lite-preview")
except:
    st.error("API Key 讀取失敗")
    st.stop()

st.set_page_config(page_title="I Japanese 練習器")

# --- 核心播放函數 (最直接的 HTML 寫法) ---
def play_audio(text):
    # 直接在 HTML 組件裡執行，不轉彎
    html_code = f"""
    <div id="player"></div>
    <script>
        (function() {{
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance('{text}');
            msg.lang = 'ja-JP';
            msg.rate = 0.9;
            window.speechSynthesis.speak(msg);
        }})();
    </script>
    """
    st.components.v1.html(html_code, height=0)

# --- 讀取教材 ---
save_path = "Japanese_Lessons"
if not os.path.exists(save_path):
    st.error("找不到教材資料夾")
else:
    files = sorted([f for f in os.listdir(save_path) if f.endswith('.json')])
    selected_file = st.selectbox("🎯 選擇課目", files)
    with open(os.path.join(save_path, selected_file), 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    sentences = data['sentences']
    if 'idx' not in st.session_state: st.session_state.idx = 0
    
    current_s = sentences[st.session_state.idx]

    # --- 顯示與按鈕 ---
    st.subheader("📖 列表 (點擊會發聲)")
    for i, s in enumerate(sentences):
        if st.button(s, key=f"btn_{i}"):
            st.session_state.idx = i
            play_audio(s)
            # 這裡暫時不 rerun，先確認聲音能不能出來

    st.divider()
    st.write(f"當前句子：**{current_s}**")
    
    if st.button("🔈 再念一次"):
        play_audio(current_s)

    # --- 判定功能 ---
    audio_record = mic_recorder(start_prompt="🔴 錄音", stop_prompt="⬛ 判定", key="rec")
    if audio_record:
        audio_input = {"mime_type": "audio/wav", "data": audio_record['bytes']}
        response = model.generate_content([f"原文：{current_s}，請評分。", audio_input])
        st.write(response.text)
