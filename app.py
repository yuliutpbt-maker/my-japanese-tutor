import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder

# --- 1. API 基礎初始化 (維持 3.1 Flash Lite) ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("models/gemini-3.1-flash-lite-preview")
except:
    st.error("API 初始化失敗")
    st.stop()

st.title("日文練習 (穩定回歸版)")

# --- 2. 語音播放 (維持電腦版必響的 JS) ---
def play_audio(text):
    js_code = f"""
    <script>
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance('{text}');
        msg.lang = 'ja-JP';
        msg.rate = 0.9;
        window.speechSynthesis.speak(msg);
    </script>
    """
    st.components.v1.html(js_code, height=0)

# 測試句
target = "最近は仕事が忙しくて、ゆっくり休む時間がなくて困っています。"
st.info(f"目標句子：{target}")

if st.button("🔈 聽發音"):
    play_audio(target)

st.divider()

# --- 3. 穩定判定邏輯 (不使用 empty，減少卡死機會) ---
st.write("🎙️ 錄音評分：")
audio = mic_recorder(start_prompt="🔴 錄音", stop_prompt="⬛ 停止", key="stable_v4")

if audio:
    # 直接顯示進度，不切換容器
    st.write("⏳ 正在與 Gemini 連線中，請稍候...")
    
    try:
        # 指令稍微加長回「能理解」的程度，但要求精簡回答
        # 實測證明：結構完整的 Prompt 比極短的 Prompt 更快回傳
        prompt = f"請聽錄音並比對原文：『{target}』。請直接給出 SCORE: 0-100 與一句簡單的發音建議。"
        
        response = model.generate_content([
            prompt,
            {"mime_type": "audio/wav", "data": audio['bytes']}
        ])
        
        # 顯示結果
        st.success("判定完成！")
        st.write(response.text)
        
    except Exception as e:
        # 萬一卡住報錯，至少能看到原因
        st.error(f"連線異常，請檢查網路或重新錄音。錯誤訊息：{e}")
