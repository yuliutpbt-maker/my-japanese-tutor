import streamlit as st
import google.generativeai as genai
import json
import os
from streamlit_mic_recorder import mic_recorder

# --- 1. 初始化與模型極速配置 ---
API_KEY = "AIzaSyCc3hu6ZAIg8jGY1EUBNIBB88xYaZdNAzI" 
genai.configure(api_key=API_KEY)

# 配置模型參數以追求最快反應速度
# temperature=0.0 可讓 AI 思考最直接，不繞圈子
model = genai.GenerativeModel(
    "models/gemini-3.1-flash-lite-preview",
    generation_config={
        "temperature": 0.0,
        "max_output_tokens": 100, # 縮短回傳內容，提升速度
    }
)

st.set_page_config(page_title="I Japanese 練習器 v1.2", layout="wide")

# v1 的預設路徑
save_path = "Japanese_Lessons"

# 初始化狀態
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0
if 'auto_speak' not in st.session_state:
    st.session_state.auto_speak = False

# --- 2. 瀏覽器語音播放 (v1 原始邏輯) ---
def play_audio(text):
    js = f"""
    <script>
    (function() {{
        var msg = new SpeechSynthesisUtterance('{text}');
        msg.lang = 'ja-JP';
        msg.rate = 0.85;
        var voices = window.speechSynthesis.getVoices();
        var jaVoice = voices.find(v => v.lang === 'ja-JP' || v.lang.includes('ja'));
        if (jaVoice) {{ msg.voice = jaVoice; }}
        window.speechSynthesis.speak(msg);
    }})();
    </script>
    """
    st.components.v1.html(js, height=0)

# --- 3. 讀取教材 ---
if not os.path.exists(save_path):
    st.error(f"路徑錯誤：{save_path}")
else:
    files = [f for f in os.listdir(save_path) if f.endswith('.json')]
    if not files:
        st.warning("請先生成教材內容。")
    else:
        selected_file = st.selectbox("🎯 選擇練習課目", files)
        with open(os.path.join(save_path, selected_file), 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        sentences = data['sentences']
        idx = st.session_state.current_idx
        current_s = sentences[idx]

        # --- 4. 全文顯示 (支援點擊跳轉) ---
        st.subheader("📖 全文預覽")
        full_text_container = st.container()
        with full_text_container:
            for i, s in enumerate(sentences):
                is_active = (i == idx)
                if st.button(s, key=f"v1_btn_{i}", type="primary" if is_active else "secondary"):
                    st.session_state.current_idx = i
                    st.session_state.auto_speak = True
                    st.rerun()

        st.divider()

        # 切換句子時自動播放
        if st.session_state.auto_speak:
            play_audio(current_s)
            st.session_state.auto_speak = False

        # --- 5. 核心互動區 ---
        st.markdown(f"### 🎯 當前練習句子 ({idx+1}/{len(sentences)})")
        st.info(current_s)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔈 重複聽範例"):
                play_audio(current_s)
        with c2:
            if st.button("⏭️ 跳下一句"):
                st.session_state.current_idx = (idx + 1) % len(sentences)
                st.rerun()

        # --- 6. 極速錄音判定區 ---
        st.write("---")
        st.markdown("#### 🎙️ 錄音判定")
        
        # 動態 Key 解決誤觸問題
        record_key = f"v1_fast_recorder_{idx}"
        audio_record = mic_recorder(
            start_prompt="🔴 開始錄音",
            stop_prompt="⬛ 結束並判定",
            key=record_key
        )

        if audio_record and 'bytes' in audio_record:
            # 建立一個佔位符，顯示即時狀態
            status_placeholder = st.empty()
            status_placeholder.warning("⚡ 正在分析...")
            
            try:
                # 極簡化 Prompt，讓 AI 直奔主題減少計算時間
                prompt = f"比對「{current_s}」。聽音評分給 SCORE:0-100 與簡短日語建議 ADVICE。"
                audio_input = {"mime_type": "audio/wav", "data": audio_record['bytes']}
                
                response = model.generate_content([prompt, audio_input])
                
                status_placeholder.empty() # 判定完畢即清除狀態
                st.markdown("##### 📊 判定結果")
                st.write(response.text)
                
                if "SCORE:" in response.text:
                    # 簡易判斷是否有達到 70 分
                    st.balloons()
            except Exception as e:
                status_placeholder.error(f"判定失敗: {e}")