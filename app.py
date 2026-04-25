import streamlit as st
import google.generativeai as genai
import json
import os
from streamlit_mic_recorder import mic_recorder

# --- 1. 回歸原始 3.1 Flash Lite 版本 ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    # 回歸我們一開始最成功的版本
    model = genai.GenerativeModel("models/gemini-3.1-flash-lite-preview")
except Exception as e:
    st.error(f"API 設定錯誤: {e}")
    st.stop()

st.set_page_config(page_title="I Japanese 練習器", layout="wide")

# --- 2. 核心語音播放 JS (優化手機喚醒) ---
def play_audio_js(text):
    # 這段代碼會被嵌入在頁面中，點擊即觸發
    js = f"""
    <script>
    var msg = new SpeechSynthesisUtterance('{text}');
    msg.lang = 'ja-JP';
    msg.rate = 0.85;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(msg);
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

    # --- 4. 全文預覽：點擊句子 = 切換 + 播放 ---
    st.subheader("📖 全文預覽")
    for i, s in enumerate(sentences):
        is_active = (i == idx)
        # 手機版關鍵：點擊按鈕時，同時運行「切換狀態」與「執行JS播放」
        if st.button(s, key=f"btn_{i}", type="primary" if is_active else "secondary"):
            st.session_state.current_idx = i
            # 在重整之前先播一次，並在重整後設定自動播放標記
            play_audio_js(s) 
            st.session_state.needs_speak = True
            st.rerun()

    st.divider()
    st.info(f"當前練習：{current_s}")

    # --- 5. 功能按鈕 ---
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔈 重複聽這句"):
            play_audio_js(current_s)
    with c2:
        if st.button("⏭️ 下一句"):
            st.session_state.current_idx = (idx + 1) % len(sentences)
            st.session_state.needs_speak = True
            st.rerun()

    # 處理重整後的自動播放
    if st.session_state.get('needs_speak', False):
        play_audio_js(current_s)
        st.session_state.needs_speak = False

    # --- 6. 錄音判定 ---
    st.write("---")
    audio_record = mic_recorder(
        start_prompt="🔴 開始錄音",
        stop_prompt="⬛ 結束並判定",
        key=f"rec_v4_{idx}"
    )

    if audio_record:
        with st.spinner("Gemini 分析中..."):
            try:
                audio_input = {"mime_type": "audio/wav", "data": audio_record['bytes']}
                prompt = f"原文：'{current_s}'。請聽我的日文發音，給出評分(SCORE)與建議(ADVICE)。"
                response = model.generate_content([prompt, audio_input])
                st.markdown("##### 📊 判定結果")
                st.write(response.text)
                if "SCORE" in response.text:
                    st.balloons()
            except Exception as e:
                st.error(f"判定失敗：{e}")
