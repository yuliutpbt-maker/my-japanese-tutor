import streamlit as st
import google.generativeai as genai
import json
import os
import time
from streamlit_mic_recorder import mic_recorder

# --- 1. API 初始化 ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("models/gemini-3.1-flash-lite-preview")
except Exception as e:
    st.error(f"API 設定錯誤: {e}")
    st.stop()

st.set_page_config(page_title="I Japanese 練習器", layout="wide")

# --- 2. 狀態初始化 ---
if 'idx' not in st.session_state:
    st.session_state.idx = 0
if 'speak_text' not in st.session_state:
    st.session_state.speak_text = ""

# --- 3. 終極發音補丁：直接在主頁面輸出 JS ---
# 只要 speak_text 有變動，這段 JS 就會重新執行一次
if st.session_state.speak_text:
    js_code = f"""
    <script>
        (function() {{
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance("{st.session_state.speak_text}");
            msg.lang = 'ja-JP';
            msg.rate = 0.9;
            window.speechSynthesis.speak(msg);
        }})();
    </script>
    """
    st.components.v1.html(js_code, height=0)
    # 執行完後清空，避免重複播放
    st.session_state.speak_text = ""

# --- 4. 讀取教材 ---
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
                st.session_state.speak_text = s # 觸發發音
                st.rerun()

        st.divider()
        st.markdown(f"### 🎯 當前練習：\n#### {current_s}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔈 重複聽這句", use_container_width=True):
                st.session_state.speak_text = current_s # 觸發發音
                st.rerun()
        with col2:
            if st.button("⏭️ 下一句", use_container_width=True):
                st.session_state.idx = (idx + 1) % len(sentences)
                st.rerun()

        # --- 6. 錄音判定區 ---
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
                except Exception as e:
                    st.error(f"分析失敗：{e}")
                    
