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

st.title("日文練習 (多媒體強制解鎖版)")

# --- 2. 核心：強制發聲函數 ---
def play_audio(text):
    # 使用 Google TTS 的穩定接口
    tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={text}&tl=ja&client=tw-ob"
    
    # 這是最強大的 HTML5 播放寫法
    # 加入 playsinline 和 controls 雖然會顯示播放器，但最能避開手機攔截
    audio_html = f"""
        <div style="background:#f0f2f6; padding:10px; border-radius:5px;">
            <p style="margin:0; font-size:14px; color:#555;">正在準備音訊...</p>
            <audio autoplay controls style="width: 100%; height: 30px;">
                <source src="{tts_url}" type="audio/mpeg">
                您的瀏覽器不支援音訊播放。
            </audio>
        </div>
        <script>
            var audio = document.querySelector('audio');
            audio.play().catch(function(error) {{
                console.log("自動播放被攔截，請手動點擊播放按鈕");
            }});
        </script>
    """
    st.components.v1.html(audio_html, height=80)

# --- 3. 介面 ---
target = st.text_input("輸入日文：", "こんにちは")

if st.button("🔈 撥放聲音"):
    play_audio(target)

st.divider()

# --- 4. 判定功能 ---
audio = mic_recorder(start_prompt="🔴 錄音", stop_prompt="⬛ 判定", key="v_final_mobile")

if audio:
    with st.spinner("分析中..."):
        try:
            response = model.generate_content([
                f"原文：『{target}』。請判定發音。",
                {"mime_type": "audio/wav", "data": audio['bytes']}
            ])
            st.success("結果：")
            st.write(response.text)
        except Exception as e:
            st.error(f"分析失敗：{e}")
