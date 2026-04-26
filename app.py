import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder

# 1. API 初始化 (穩定的 3.1 Flash Lite)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("models/gemini-3.1-flash-lite-preview")
except:
    st.error("API 密鑰遺失或錯誤")
    st.stop()

# 2. 穩定的發聲函數 (電腦版必響)
def play_audio(text):
    js = f"""<script>
        window.speechSynthesis.cancel();
        var m = new SpeechSynthesisUtterance('{text}');
        m.lang = 'ja-JP';
        window.speechSynthesis.speak(m);
    </script>"""
    st.components.v1.html(js, height=0)

st.title("📖 日文文章朗讀練習")

# 3. 文章段落區域 (讓你清楚看著字)
article_text = """最近は仕事が忙しくて、ゆっくり休む時間がなくて困っています。
来週からは少し余裕ができるはずなので、友達と旅行に行く計画を立てています。"""

# 將文章拆成句子，方便逐句練習
sentences = [s.strip() for s in article_text.split('\n') if s.strip()]

for i, s in enumerate(sentences):
    with st.expander(f"句子 {i+1}：{s[:15]}...", expanded=(i==0)):
        st.write(f"### {s}") # 讓字很大，看得清楚
        
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button(f"🔈 聽發音", key=f"play_{i}"):
                play_audio(s)
        
        with col2:
            # 這是 11:00 最穩定的錄音 Key 結構
            audio = mic_recorder(start_prompt="🔴 錄音", stop_prompt="⬛ 判定", key=f"rec_{i}")
            
            if audio:
                st.write("⏳ 正在分析...")
                try:
                    # 恢復最原始、不卡死的 Prompt
                    response = model.generate_content([
                        f"原文：『{s}』。請判定發音並給分與建議。",
                        {"mime_type": "audio/wav", "data": audio['bytes']}
                    ])
                    st.info(response.text)
                except Exception as e:
                    st.error(f"分析逾時，請再試一次")
