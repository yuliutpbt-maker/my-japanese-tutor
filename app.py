import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder

# --- 1. 初始化 (維持 3.1 Flash Lite) ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("models/gemini-3.1-flash-lite-preview")
except:
    st.error("API 設定錯誤")
    st.stop()

st.set_page_config(page_title="極速日語打分")

# --- 2. 語音播放 (電腦穩定版) ---
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
n3_sentence = "最近は仕事が忙しくて、ゆっくり休む時間がなくて困っています。"
target = st.text_area("練習句子：", n3_sentence, height=70)

if st.button("🔈 聽發音"):
    play_audio(target)

st.divider()

# --- 4. 極速判定 (只看分數) ---
st.write("🎙️ 錄音評分：")
audio = mic_recorder(start_prompt="🔴 錄音", stop_prompt="⬛ 停止", key="ultra_fast_rec")

if audio:
    # 使用佔位符，讓分數直接蓋過進度條
    status = st.empty()
    status.write("⚡ 評分中...")
    
    try:
        # 強制只輸出分數，這會讓 Gemini 反應極快
        fast_prompt = f"原文：『{target}』。請聽錄音，只回傳一個數字分數 (0-100)，不要任何文字。"
        
        response = model.generate_content([
            fast_prompt,
            {"mime_type": "audio/wav", "data": audio['bytes']}
        ])
        
        status.empty()
        score_text = response.text.strip()
        
        # 大字顯示分數
        st.markdown(f"<h1 style='text-align: center; color: #1E90FF;'>{score_text} 分</h1>", unsafe_allow_html=True)
        
        if score_text.isdigit() and int(score_text) > 80:
            st.balloons()
            
    except Exception as e:
        status.error(f"錯誤：{e}")
