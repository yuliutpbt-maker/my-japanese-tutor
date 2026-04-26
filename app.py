import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder

# --- 1. 初始化 ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("models/gemini-3.1-flash-lite-preview")
except:
    st.error("API 初始化失敗")
    st.stop()

st.set_page_config(page_title="日語判定器")

# --- 2. 語音播放 (維持電腦版有聲) ---
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

st.title("日文練習 (穩定極速)")

# N3 測試句
target = st.text_input("練習句：", "最近は仕事が忙しくて、ゆっくり休む時間がなくて困っています。")

if st.button("🔈 聽發音"):
    play_audio(target)

st.divider()

# --- 3. 判定功能 ---
audio = mic_recorder(
    start_prompt="🔴 開始錄音", 
    stop_prompt="⬛ 停止並評分", 
    key="stable_fast_v2"
)

if audio:
    # 使用 placeholder 顯示狀態
    res_area = st.empty()
    res_area.write("⏳ 正在傳輸音檔並分析...")
    
    try:
        # 稍微完整的 Prompt 其實比極短的 Prompt 更不容易出錯
        prompt = f"請聽錄音並比對原文：『{target}』。請直接給出一個 0 到 100 的數字分數，並在後面加一個短評。"
        
        response = model.generate_content([
            prompt,
            {"mime_type": "audio/wav", "data": audio['bytes']}
        ])
        
        res_area.empty()
        st.subheader("📊 判定結果")
        st.write(response.text)
        
        if "100" in response.text or "9" in response.text: # 簡單判定高分
            st.balloons()
            
    except Exception as e:
        res_area.error(f"發生錯誤：{e}")
