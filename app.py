import streamlit as st
import google.generativeai as genai
import json
import os
import time
from streamlit_mic_recorder import mic_recorder

# --- 1. API 初始化 (100% 還原睡前版) ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("models/gemini-3.1-flash-lite-preview")
except Exception as e:
    st.error(f"API 設定錯誤: {e}")
    st.stop()

st.set_page_config(page_title="I Japanese 練習器", layout="wide")

# --- 2. 核心修正：加入 iOS 空播喚醒補丁的發音函數 ---
def play_audio(text):
    # 這個版本會先發出一個無聲指令來「踢開」瀏覽器的音訊限制門
    js_code = f"""
    <script>
        (function() {{
            // 1. 先重置所有語音
            window.speechSynthesis.cancel();
            
            // 2. 建立一個空的語音物件，這是一個「敲門」動作，用來解鎖 iOS 權限
            var whisper = new SpeechSynthesisUtterance("");
            window.speechSynthesis.speak(whisper);
            
            // 3. 準備真正的日文語音
            var msg = new SpeechSynthesisUtterance('{text}');
            msg.lang = 'ja-JP';
            msg.rate = 0.9;  // 稍微放慢，比較自然
            msg.pitch = 1.0;
            
            // 4. 延遲 50 毫秒播放，確保「門」已經被踢開了
            setTimeout(function() {{
                window.speechSynthesis.speak(msg);
            }}, 50);
        }})();
    </script>
    """
    st.components.v1.html(js_code, height=0)

# --- 3. 狀態初始化 ---
if 'idx' not in st.session_state:
    st.session_state.idx = 0

# --- 4. 讀取教材 (Japanese_Lessons) ---
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

        # --- 6. 錄音判定區 (v8 穩定邏輯) ---
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
