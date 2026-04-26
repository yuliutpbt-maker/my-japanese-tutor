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

# --- 2. 仿真 MDN 測試頁面的發音函數 ---
def play_audio(text):
    js_code = f"""
    <script>
        (function() {{
            window.speechSynthesis.cancel();
            
            // 模仿 MDN 成功的關鍵：先執行一次 getVoices
            var voices = window.speechSynthesis.getVoices();
            
            var msg = new SpeechSynthesisUtterance('{text}');
            msg.lang = 'ja-JP';
            msg.rate = 0.9;
            
            // iOS 必須在 user gesture 裡面執行，且有時候需要微小的延遲
            if (speechSynthesis.speaking) {{
                window.speechSynthesis.cancel();
            }}
            
            // 嘗試播放
            window.speechSynthesis.speak(msg);
            
            // 補丁：如果 0.5 秒後還沒在說話，再補一槍
            setTimeout(function() {{
                if (!window.speechSynthesis.speaking) {{
                    window.speechSynthesis.speak(msg);
                }}
            }}, 500);
        }})();
    </script>
    """
    st.components.v1.html(js_code, height=0)

# --- 3. 狀態初始化 ---
if 'idx' not in st.session_state:
    st.session_state.idx = 0

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
                play_audio(s) 
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
                    if "SCORE" in response.text:
                        st.balloons()
                except Exception as e:
                    st.error(f"分析失敗：{e}")
