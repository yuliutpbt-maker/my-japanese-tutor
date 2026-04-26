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

# --- 2. 核心修正：使用 JS Audio 物件 (Google 自然人聲，不產生 ID 衝突) ---
def play_google_audio(text):
    # 使用 JavaScript 的新物件來播放，這比 HTML 標籤更穩定，不會被 Streamlit 報錯
    tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={text}&tl=ja&client=tw-ob"
    js_code = f"""
    <script>
        (function() {{
            var audio = new Audio('{tts_url}');
            audio.play().catch(function(error) {{
                console.log("播放被攔截，通常是因為需要使用者先點擊頁面:", error);
            }});
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
                # 點擊後，先發聲再刷新
                play_google_audio(s)
                time.sleep(0.2)
                st.rerun()

        st.divider()
        st.markdown(f"### 🎯 當前練習：\n#### {current_s}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔈 重複聽這句", use_container_width=True):
                play_google_audio(current_s)
        with col2:
            if st.button("⏭️ 下一句", use_container_width=True):
                st.session_state.idx = (idx + 1) % len(sentences)
                st.rerun()

        # --- 6. 錄音判定區 (還原 v8 穩定邏輯) ---
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
                    instruction = f"請比對日文原文『{current_s}』。給出 SCORE:0-100 與 ADVICE。"
                    response = model.generate_content([instruction, audio_blob])
                    st.success("✅ 分析完畢")
                    st.write(response.text)
                    if "SCORE" in response.text:
                        st.balloons()
                except Exception as e:
                    st.error(f"分析失敗：{e}")
