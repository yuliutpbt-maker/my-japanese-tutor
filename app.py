import streamlit as st
import google.generativeai as genai
import json
import os
from streamlit_mic_recorder import mic_recorder

# --- 1. 安全初始化 ---
try:
    # 確保這裡的名稱與你在 Secrets 設定的一模一樣
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    # 使用最穩定的 1.5 Flash 模型，反應速度也很快
    model = genai.GenerativeModel("gemini-1.5-flash")
except Exception as e:
    st.error(f"API 設定錯誤: {e}")
    st.stop()

st.set_page_config(page_title="I Japanese 練習器", layout="wide")

# --- 2. 手機優化版語音 (支援 iOS 強制播放) ---
def play_audio(text):
    # 這段 JS 會先嘗試喚醒語音引擎
    js = f"""
    <script>
    (function() {{
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance('{text}');
        msg.lang = 'ja-JP';
        msg.rate = 0.9;
        
        // iOS 必須在 user gesture 內觸發，這裏增加重試機制
        function speak() {{
            window.speechSynthesis.speak(msg);
        }}
        
        if (window.speechSynthesis.getVoices().length === 0) {{
            window.speechSynthesis.onvoiceschanged = speak;
        }} else {{
            speak();
        }}
    }})();
    </script>
    """
    st.components.v1.html(js, height=0)

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

    # --- 4. 介面介面 ---
    st.subheader("📖 全文預覽")
    for i, s in enumerate(sentences):
        if st.button(s, key=f"btn_{i}", type="primary" if i==idx else "secondary"):
            st.session_state.current_idx = i
            play_audio(s) # 點擊後直接播放，符合手機權限
            st.rerun()

    st.divider()
    st.info(f"當前練習：{current_s}")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔈 聽範例音"):
            play_audio(current_s)
    with c2:
        if st.button("⏭️ 下一句"):
            st.session_state.current_idx = (idx + 1) % len(sentences)
            st.rerun()

    # --- 5. 錄音判定 ---
    st.write("---")
    audio_record = mic_recorder(
        start_prompt="🔴 開始錄音",
        stop_prompt="⬛ 結束判定",
        key=f"rec_{idx}"
    )

    if audio_record:
        with st.spinner("Gemini 判定中..."):
            try:
                # 傳送錄音數據
                audio_data = {"mime_type": "audio/wav", "data": audio_record['bytes']}
                prompt = f"原文：'{current_s}'。請聽我的日文發音，給出評分(SCORE)與建議(ADVICE)。"
                
                response = model.generate_content([prompt, audio_data])
                st.markdown("##### 📊 判定結果")
                st.write(response.text)
                if "SCORE" in response.text:
                    st.balloons()
            except Exception as e:
                # 這裡會顯示更詳細的錯誤訊息，方便我們診斷
                st.error(f"判定出錯：{str(e)}")
