import streamlit as st
import google.generativeai as genai
import json
import os
from streamlit_mic_recorder import mic_recorder

# --- 1. API 初始化 (回歸 3.1 版) ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("models/gemini-3.1-flash-lite-preview")
except Exception as e:
    st.error(f"API 設定錯誤: {e}")
    st.stop()

st.set_page_config(page_title="I Japanese 練習器", layout="wide")

# --- 2. 原始電腦版語音方案 (V1 邏輯) ---
def play_audio(text):
    # 這是你最初電腦版能動的唯一寫法
    js = f"""
    <script>
    (function() {{
        var msg = new SpeechSynthesisUtterance('{text}');
        msg.lang = 'ja-JP';
        msg.rate = 0.85;
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(msg);
    }})();
    </script>
    """
    st.components.v1.html(js, height=0)

# --- 3. 教材路徑與狀態 ---
save_path = "Japanese_Lessons"
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0

# --- 4. 讀取教材 ---
if not os.path.exists(save_path):
    st.error("找不到教材資料夾")
else:
    files = sorted([f for f in os.listdir(save_path) if f.endswith('.json')])
    selected_file = st.selectbox("🎯 選擇練習課目", files)
    with open(os.path.join(save_path, selected_file), 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    sentences = data['sentences']
    idx = st.session_state.current_idx
    current_s = sentences[idx]

    # --- 5. 介面操作 (回歸原始點擊邏輯) ---
    st.subheader("📖 點擊句子播放")
    
    for i, s in enumerate(sentences):
        if st.button(s, key=f"v1_btn_{i}", type="primary" if i == idx else "secondary"):
            st.session_state.current_idx = i
            play_audio(s) # 電腦版點擊後直接執行 JS 播放
            st.rerun()

    st.divider()

    st.info(f"當前句子：{current_s}")

    if st.button("🔈 重複聽這句"):
        play_audio(current_s)

    if st.button("⏭️ 下一句"):
        st.session_state.current_idx = (idx + 1) % len(sentences)
        st.rerun()

    # --- 6. 錄音判定 ---
    st.write("---")
    audio_record = mic_recorder(
        start_prompt="🔴 開始錄音",
        stop_prompt="⬛ 結束並判定",
        key=f"rec_v1_{idx}"
    )

    if audio_record:
        with st.spinner("判定中..."):
            try:
                audio_input = {"mime_type": "audio/wav", "data": audio_record['bytes']}
                prompt = f"原文：'{current_s}'。請聽我的發音，給出 SCORE:0-100 與 ADVICE。"
                response = model.generate_content([prompt, audio_input])
                st.write(response.text)
                if "SCORE" in response.text:
                    st.balloons()
            except Exception as e:
                st.error(f"判定失敗: {e}")
