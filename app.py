import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder

# --- 1. API 初始化 ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("models/gemini-3.1-flash-lite-preview")
except:
    st.error("API 設定錯誤")
    st.stop()

st.set_page_config(page_title="日語口說極速判定", layout="wide")

# --- 2. 核心語音腳本 (電腦穩定版) ---
def play_audio(text):
    js_fixed = f"""
    <script>
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance('{text}');
        msg.lang = 'ja-JP';
        msg.rate = 0.85;
        window.speechSynthesis.speak(msg);
    </script>
    """
    st.components.v1.html(js_fixed, height=0)

st.title("N3 日語極速練習")

# N3 測試長句
n3_sentence = "最近は仕事が忙しくて、ゆっくり休む時間がなくて困っています。"
target = st.text_area("練習句子：", n3_sentence, height=80)

if st.button("🔈 聽發音"):
    play_audio(target)

st.divider()

# --- 3. 極速判定邏輯 ---
st.write("🎙️ 錄音並立即評分：")
audio = mic_recorder(start_prompt="🔴 錄音", stop_prompt="⬛ 停止", key="fast_rec")

if audio:
    with st.spinner("評分中..."):
        try:
            # 這是關鍵：強制 Gemini 只輸出核心資訊，減少生成時間
            fast_prompt = f"""
            原文：『{target}』
            請僅針對錄音回傳：
            1. SCORE: 0-100
            2. 發音短評：(20字以內)
            3. 語調短評：(20字以內)
            """
            
            response = model.generate_content([
                fast_prompt,
                {"mime_type": "audio/wav", "data": audio['bytes']}
            ])
            
            # 顯示結果
            st.subheader("📊 判定結果")
            st.info(response.text)
            
            if "SCORE" in response.text:
                st.balloons()
                
        except Exception as e:
            st.error(f"分析失敗：{e}")

# --- 📱 手機沒聲音的最終提醒 ---
# 因為你手機沒有實體開關，若電腦有聲手機沒聲，請檢查：
# 1. 滑下控制中心 (右上角拉下)
# 2. 確認「鈴鐺圖示」不是紅色的（如果是紅色，網頁發音會被封鎖）
# 3. 點擊「聽發音」按鈕來解鎖瀏覽器權限
