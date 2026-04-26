import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder

# --- 1. 初始化 (維持 3.1 Flash Lite) ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # 確保使用 flash-lite，這是目前反應最快的模型
    model = genai.GenerativeModel("models/gemini-3.1-flash-lite-preview")
except:
    st.error("API 設定錯誤")
    st.stop()

st.set_page_config(page_title="極速打分")

# --- 2. 語音播放 ---
def play_audio(text):
    js = f"""
    <script>
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance('{text}');
        msg.lang = 'ja-JP';
        window.speechSynthesis.speak(msg);
    </script>
    """
    st.components.v1.html(js, height=0)

# --- 3. 介面 ---
target = st.text_input("練習句：", "最近は仕事が忙しくて、ゆっくり休む時間がなくて困っています。")

if st.button("🔈 聽發音"):
    play_audio(target)

st.divider()

# --- 4. 針對 10 秒延遲的優化判定 ---
st.write("🎙️ 錄音評分：")
# 限制錄音長度可以減少上傳時間
audio = mic_recorder(start_prompt="🔴 錄音", stop_prompt="⬛ 停止", key="fast_v1")

if audio:
    # 立即變更畫面狀態，減少「等死」的感覺
    container = st.empty()
    container.markdown("### ⚡ 正在計算分數...")
    
    try:
        # 強制 Gemini 進入「直接輸出」模式
        # 加上 "Result only" 的指令能減少 AI 內部的 Reasoning 時間
        response = model.generate_content([
            f"Result only. Score 0-100 for pronunciation of: {target}",
            {"mime_type": "audio/wav", "data": audio['bytes']}
        ], generation_config={"max_output_tokens": 5}) # 限制輸出字數也能縮短時間
        
        score = response.text.strip()
        container.markdown(f"<h1 style='text-align: center; font-size: 80px; color: #1E90FF;'>{score}</h1>", unsafe_allow_html=True)
        
    except Exception as e:
        container.error(f"連線超時：{e}")
