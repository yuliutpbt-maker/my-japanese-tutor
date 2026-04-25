import streamlit as st
import google.generativeai as genai
import json
import os
from streamlit_mic_recorder import mic_recorder

# --- 1. 回歸原始 3.1 Flash Lite 版本 (最穩定的判定版) ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("models/gemini-3.1-flash-lite-preview")
except Exception as e:
    st.error(f"API 設定錯誤: {e}")
    st.stop()

st.set_page_config(page_title="I Japanese 練習器", layout="wide")

# --- 2. 萬能聲音解鎖腳本 (針對手機 Safari/Chrome 優化) ---
def init_audio_js():
    # 這段 JS 會在網頁加載時執行，並在使用者第一次點擊時解鎖聲音引擎
    js = """
    <script>
    if (!window.audioUnlocked) {
        window.addEventListener('click', function() {
            var msg = new SpeechSynthesisUtterance('');
            msg.volume = 0; // 靜音播放一次
            window.speechSynthesis.speak(msg);
            window.audioUnlocked = true;
            console.log("Audio Unlocked");
        }, { once: true });
    }
    </script>
    """
    st.components.v1.html(js, height=0)

def play_audio_js(text):
    js = f"""
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
    st.components.v1.html(js, height=0)

# 啟動解鎖腳本
init_audio_js()

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

    # --- 4. 全文顯示區 ---
    st.subheader("📖 全文預覽")
    for i, s in enumerate(sentences):
        if st.button(s, key=f"btn_{i}", type="primary" if i==idx else "secondary"):
            st.session_state.current_idx = i
            play_audio_js(s) # 直接播放
            st.rerun()

    st.divider()

    # --- 5. 互動區 ---
    st.info(f"當前練習：{current_s}")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔈 重複聽範例"):
            play_audio_js(current_s)
    with c2:
        if st.button("⏭️ 下一句"):
            st.session_state.current_idx = (idx + 1) % len(sentences)
            st.rerun()

    # --- 6. 錄音判定 ---
    st.write("---")
    audio_record = mic_recorder(
        start_prompt="🔴 開始錄音",
        stop_prompt="⬛ 結束並判定",
        key=f"rec_deploy_{idx}"
    )

    if audio_record:
        with st.spinner("Gemini 正在分析..."):
            try:
                audio_input = {"mime_type": "audio/wav", "data": audio_record['bytes']}
                prompt = f"原文：'{current_s}'。請聽我的日文發音，給出評分(SCORE:0-100)與簡短建議(ADVICE)。"
                response = model.generate_content([prompt, audio_input])
                st.markdown("##### 📊 判定結果")
                st.write(response.text)
                if "SCORE" in response.text:
                    st.balloons()
            except Exception as e:
                st.error(f"判定失敗：{e}")
