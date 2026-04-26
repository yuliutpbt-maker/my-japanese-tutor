import streamlit as st
import google.generativeai as genai
import json
import os
import time
from streamlit_mic_recorder import mic_recorder

# --- 1. API 初始化 (100% 還原) ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("models/gemini-3.1-flash-lite-preview")
except Exception as e:
    st.error(f"API 設定錯誤: {e}")
    st.stop()

st.set_page_config(page_title="I Japanese 練習器", layout="wide")

# --- 2. 萬用發音函數 (回歸原生 API，保證出聲) ---
def play_audio(text):
    # 使用原生 Web Speech API，這是睡前穩定版的基礎
    # 我們加入語音篩選邏輯，試圖找出系統中最自然的日文聲音
    js_code = f"""
    <script>
        (function() {{
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance('{text}');
            msg.lang = 'ja-JP';
            
            // 語音引擎優化：嘗試抓取系統中品質較好的日文人聲
            var voices = window.speechSynthesis.getVoices();
            var jaVoice = voices.find(v => v.lang.includes('ja') && v.name.includes('Google'));
            if (jaVoice) msg.voice = jaVoice;
            
            msg.rate = 0.85; // 稍微放慢一點，聽起來更清楚自然
            msg.pitch = 1.0;
            window.speechSynthesis.speak(msg);
        }})();
    </script>
    """
    st.components.v1.html(js_code, height=0)

# --- 3. 狀態初始化 ---
if 'idx' not in st.session_state:
    st.session_state.idx = 0

# --- 4. 讀取教材 (資料夾：Japanese_Lessons) ---
save_path = "Japanese_Lessons"

if not os.path.exists(save_path):
    st.error(f"找不到教材資料夾：{save_path}")
else:
    files = sorted([f for f in os.listdir(save_path) if f.endswith('.json')])
    if not files:
        st.warning("資料夾內沒有教材檔")
    else:
        selected_file = st.selectbox("🎯 選擇練習課目", files)
        with open(os.path.join(save_path, selected_file), 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        sentences = data['sentences']
        idx = st.session_state.idx
        current_s = sentences[idx]

        # --- 5. 介面設計 ---
        st.subheader("📖 全文預覽")
        for i, s in enumerate(sentences):
            if st.button(s, key=f"list_btn_{i}", type="primary" if i == idx else "secondary", use_container_width=True):
                st.session_state.idx = i
                play_audio(s) # 點擊全文直接發音
                time.sleep(0.1)
                st.rerun()

        st.divider()
        st.markdown(f"### 🎯 當前練習：\n#### {current_s}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔈 重複聽這句", use_container_width=True):
                play_audio(current_s)
        with col2:
            if st.button("⏭️ 下一句", use_container_width=True):
                st.session_state.idx = (idx + 1) % len(sentences)
                st.rerun()

        # --- 6. 錄音判定區 (v8 穩定版) ---
        st.write("---")
        st.markdown("#### 🎙️ 錄音判定")
        audio_record = mic_recorder(
            start_prompt="🔴 開始錄音",
            stop_prompt="⬛ 結束並判定",
            key=f"rec_v8_{idx}" 
        )

        if audio_record and 'bytes' in audio_record:
            with st.spinner("🚀 Gemini 3.1 正在分析..."):
                try:
                    audio_blob = {"mime_type": "audio/wav", "data": audio_record['bytes']}
                    instruction = f"原文『{current_s}』。請給分 SCORE:0-100 與建議。"
                    response = model.generate_content([instruction, audio_blob])
                    st.info(response.text)
                    if "SCORE" in response.text:
                        st.balloons()
                except Exception as e:
                    st.error(f"分析失敗：{e}")
