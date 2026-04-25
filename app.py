import streamlit as st
import google.generativeai as genai
import json
import os
from streamlit_mic_recorder import mic_recorder

# --- 1. 安全初始化 (使用 Secrets) ---
# 這樣就算 GitHub 是公開的，你的 Key 也不會被封鎖
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("請在 Streamlit Cloud 的 Secrets 中設定 GEMINI_API_KEY")
    st.stop()

genai.configure(api_key=API_KEY)

# 配置最快反應模型
model = genai.GenerativeModel(
    "models/gemini-3.1-flash-lite-preview",
    generation_config={
        "temperature": 0.0,
        "max_output_tokens": 150,
    }
)

st.set_page_config(page_title="I Japanese 練習器", layout="wide")

# --- 2. 雲端路徑設定 ---
# 這裡指向你上傳到 GitHub 的資料夾
save_path = "Japanese_Lessons"

if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0
if 'auto_speak' not in st.session_state:
    st.session_state.auto_speak = False

# --- 3. 手機優化版語音播放 ---
def play_audio(text):
    # 加入 window.speechSynthesis.cancel() 確保連按時能反應
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

# --- 4. 讀取教材 ---
if not os.path.exists(save_path):
    st.error(f"找不到教材資料夾：{{save_path}}。請確認 GitHub 上有這個資料夾且內含 JSON 檔。")
else:
    files = [f for f in os.listdir(save_path) if f.endswith('.json')]
    if not files:
        st.warning("資料夾內無教材。")
    else:
        selected_file = st.selectbox("🎯 選擇練習課目", files)
        with open(os.path.join(save_path, selected_file), 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        sentences = data['sentences']
        idx = st.session_state.current_idx
        current_s = sentences[idx]

        # --- 5. 全文與練習區 ---
        st.subheader("📖 全文預覽 (點擊句子練習)")
        full_text_container = st.container()
        with full_text_container:
            for i, s in enumerate(sentences):
                if st.button(s, key=f"btn_{i}", type="primary" if i==idx else "secondary"):
                    st.session_state.current_idx = i
                    st.session_state.auto_speak = True
                    st.rerun()

        st.divider()

        if st.session_state.auto_speak:
            play_audio(current_s)
            st.session_state.auto_speak = False

        st.markdown(f"### 🎯 當前練習：\n**{current_s}**")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔈 重複聽範例"):
                play_audio(current_s)
        with c2:
            if st.button("⏭️ 下一句"):
                st.session_state.current_idx = (idx + 1) % len(sentences)
                st.rerun()

        # --- 6. 錄音判定 ---
        st.write("---")
        record_key = f"rec_idx_{idx}"
        audio_record = mic_recorder(
            start_prompt="🔴 開始錄音",
            stop_prompt="⬛ 結束並判定",
            key=record_key
        )

        if audio_record:
            status_p = st.empty()
            status_p.warning("⚡ 判定中...")
            try:
                prompt = f"比對「{{current_s}}」。聽音評分給 SCORE:0-100 與簡短日語建議 ADVICE。"
                audio_input = {{"mime_type": "audio/wav", "data": audio_record['bytes']}}
                response = model.generate_content([prompt, audio_input])
                status_p.empty()
                st.markdown("##### 📊 判定結果")
                st.write(response.text)
                if "SCORE:" in response.text:
                    st.balloons()
            except Exception as e:
                status_p.error(f"判定出錯：{{e}}")
