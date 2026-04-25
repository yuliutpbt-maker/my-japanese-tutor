import streamlit as st
import google.generativeai as genai
import json
import os
from streamlit_mic_recorder import mic_recorder

# --- 1. API 初始化 ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("models/gemini-3.1-flash-lite-preview")
except:
    st.error("API Key 讀取失敗，請檢查 Streamlit Secrets 設定。")
    st.stop()

st.set_page_config(page_title="I Japanese 練習器", layout="wide")

# --- 2. 穩定播放函數 ---
def play_audio(text):
    html_code = f"""
    <script>
        (function() {{
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance('{text}');
            msg.lang = 'ja-JP';
            msg.rate = 0.85;
            window.speechSynthesis.speak(msg);
        }})();
    </script>
    """
    st.components.v1.html(html_code, height=0)

# --- 3. 教材路徑與狀態 ---
save_path = "Japanese_Lessons"
if 'idx' not in st.session_state:
    st.session_state.idx = 0

# --- 4. 讀取教材 ---
if not os.path.exists(save_path):
    st.error("找不到教材資料夾：Japanese_Lessons")
else:
    files = sorted([f for f in os.listdir(save_path) if f.endswith('.json')])
    selected_file = st.selectbox("🎯 選擇練習課目", files)
    
    with open(os.path.join(save_path, selected_file), 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    sentences = data['sentences']
    idx = st.session_state.idx
    current_s = sentences[idx]

    # --- 5. 介面設計 (回歸原始美觀佈局) ---
    st.subheader("📖 全文預覽")
    
    # 使用 Container 讓列表整齊
    full_text_container = st.container()
    with full_text_container:
        for i, s in enumerate(sentences):
            # 點擊即切換並發聲
            if st.button(s, key=f"list_btn_{i}", type="primary" if i == idx else "secondary", use_container_width=True):
                st.session_state.idx = i
                play_audio(s)
                st.rerun()

    st.divider()

    # 當前練習展示區
    st.markdown(f"### 🎯 當前練習：\n#### {current_s}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔈 重複聽這句", use_container_width=True):
            play_audio(current_s)
    with col2:
        if st.button("⏭️ 下一句", use_container_width=True):
            st.session_state.idx = (idx + 1) % len(sentences)
            st.rerun()

    # --- 6. 錄音判定區 ---
    st.write("---")
    st.markdown("#### 🎙️ 錄音判定")
    
    # 這裡加入錄音按鈕
    audio_record = mic_recorder(
        start_prompt="🔴 開始錄音",
        stop_prompt="⬛ 結束並判定",
        key=f"rec_vfinal_{idx}"
    )

    if audio_record:
        with st.spinner("Gemini 正在分析您的發音..."):
            try:
                audio_input = {"mime_type": "audio/wav", "data": audio_record['bytes']}
                prompt = f"原文：'{current_s}'。請聽錄音比對原文，給出 SCORE:0-100 與日語建議 ADVICE。"
                response = model.generate_content([prompt, audio_input])
                
                st.info("📊 判定結果")
                st.write(response.text)
                
                if "SCORE" in response.text:
                    st.balloons()
            except Exception as e:
                st.error(f"判定失敗：{e}")
