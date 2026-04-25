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
except:
    st.error("API 設定錯誤，請檢查 Secrets")
    st.stop()

st.set_page_config(page_title="I Japanese 練習器", layout="wide")

# --- 2. 核心聲音方案：HTML5 多媒體解鎖器 ---
def play_audio(text):
    # 使用 Google 翻譯的語音接口（這被視為「多媒體音」而非「系統語音」）
    # tl=ja 代表日文，client=tw-ob 是最穩定的公開接口
    tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={text}&tl=ja&client=tw-ob"
    
    # 這是最強大的播放腳本：它會建立一個隱形的音軌並強制播放
    audio_js = f"""
    <script>
        var audio = new Audio("{tts_url}");
        audio.play().catch(function(error) {{
            console.log("播放失敗，等待使用者互動: " + error);
        }});
    </script>
    """
    st.components.v1.html(audio_js, height=0)

# --- 3. 教材讀取 ---
save_path = "Japanese_Lessons"
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0

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

    # --- 4. 操作介面 ---
    st.subheader("📖 點擊句子即播放")
    
    for i, s in enumerate(sentences):
        # 點擊句子按鈕：直接觸發發聲，然後切換索引
        if st.button(s, key=f"s_btn_{i}", type="primary" if i == idx else "secondary"):
            st.session_state.current_idx = i
            play_audio(s) # 直接播
            st.rerun()

    st.divider()
    st.info(f"當前練習：{current_s}")

    if st.button("🔈 再念一次"):
        play_audio(current_s)

    if st.button("⏭️ 下一句"):
        st.session_state.current_idx = (idx + 1) % len(sentences)
        st.rerun()

    # --- 5. 錄音判定 ---
    st.write("---")
    audio_record = mic_recorder(
        start_prompt="🔴 開始錄音",
        stop_prompt="⬛ 結束並判定",
        key=f"rec_{idx}"
    )

    if audio_record:
        with st.spinner("判定中..."):
            try:
                audio_input = {"mime_type": "audio/wav", "data": audio_record['bytes']}
                prompt = f"原文：'{current_s}'。請聽發音給評分與建議。"
                response = model.generate_content([prompt, audio_input])
                st.write(response.text)
                if "SCORE" in response.text:
                    st.balloons()
            except Exception as e:
                st.error(f"錯誤: {e}")
