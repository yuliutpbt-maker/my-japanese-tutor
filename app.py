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

st.set_page_config(page_title="N3 日語練習 (穩定版)")

# --- 2. 核心語音腳本 (電腦恢復版) ---
def play_audio(text):
    js_code = f"""
    <script>
        window.speechSynthesis.cancel();
        var msg = new SynthesisUtterance('{text}');
        msg.lang = 'ja-JP';
        msg.rate = 0.85; // 稍微放慢一點，適合 N3 練習
        window.speechSynthesis.speak(msg);
    </script>
    """
    # 這裡修正一個剛才的小拼寫錯誤，確保 100% 執行
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

st.title("N3 日語口說挑戰")

# --- 3. N3 級別測試長句 ---
# 這句話包含：雖然...但是... (逆接)、打算 (意志)、漢字較多
n3_sentence = "最近は仕事が忙しくて、ゆっくり休む時間がなくて困っています。"

target = st.text_area("練習句子 (N3)：", n3_sentence, height=100)

if st.button("🔈 聽發音"):
    play_audio(target)

st.divider()

# --- 4. 判定功能 ---
st.write("🎙️ 請朗讀上方句子：")
audio = mic_recorder(start_prompt="🔴 開始錄音", stop_prompt="⬛ 結束並判定", key="n3_test_rec")

if audio:
    with st.spinner("Gemini 正在精細分析您的發音..."):
        try:
            # 強化 Prompt，要求針對 N3 語調給建議
            prompt = f"""
            原文：『{target}』
            請聽錄音並比對。
            1. 給出總分 SCORE:0-100
            2. 針對「漢字讀音」與「語調轉折」給出詳細建議 ADVICE。
            """
            response = model.generate_content([
                prompt,
                {"mime_type": "audio/wav", "data": audio['bytes']}
            ])
            st.success("📊 分析結果")
            st.write(response.text)
        except Exception as e:
            st.error(f"分析失敗：{e}")
