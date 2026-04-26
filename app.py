import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder

# --- 1. API 恢復 (回到 11點多那個能跑的版本) ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("models/gemini-3.1-flash-lite-preview")
except:
    st.error("API 初始化失敗")
    st.stop()

st.set_page_config(page_title="日文練習 (還原穩定版)")

# --- 2. 新嘗試：外部音訊連結發聲 (挑戰手機成功) ---
def play_audio(text):
    # 使用 Google TTS 連結，這在手機上被視為「多媒體音訊」
    tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={text}&tl=ja&client=tw-ob"
    
    # 這裡我們用 HTML5 <audio> 標籤，並加上控制項方便手動點擊（如果自動播放失敗）
    audio_html = f"""
        <div style="background:#f9f9f9; padding:5px; border-radius:5px; text-align:center;">
            <audio id="tts-audio" autoplay controls style="height: 35px; width: 100%;">
                <source src="{tts_url}" type="audio/mpeg">
            </audio>
        </div>
        <script>
            var audio = document.getElementById('tts-audio');
            audio.play().catch(function(e) {{ console.log("需手動點擊播放"); }});
        </script>
    """
    st.components.v1.html(audio_html, height=60)

st.title("日文口說 (11:00 穩定恢復版)")

# 練習句 (N3)
target = st.text_area("目標句子：", "最近は仕事が忙しくて、ゆっくり休む時間がなくて困っています。")

if st.button("🔈 聽發音 (手機請點下方播放器)"):
    play_audio(target)

st.divider()

# --- 3. 恢復 11:00 當時能動的判定邏輯 ---
st.write("🎙️ 錄音並判定：")
# 使用全新的 key (v11am) 避開之前卡死的暫存
audio = mic_recorder(start_prompt="🔴 錄音", stop_prompt="⬛ 結束並判定", key="v11am_fix")

if audio:
    with st.spinner("Gemini 正在分析音檔..."):
        try:
            # 恢復當時正常的完整指令
            prompt = f"請比對日文原文『{target}』並評分。請給出 SCORE (0-100) 與 ADVICE。"
            
            response = model.generate_content([
                prompt,
                {"mime_type": "audio/wav", "data": audio['bytes']}
            ])
            
            st.success("分析結果：")
            st.write(response.text)
            
        except Exception as e:
            st.error(f"判定發生錯誤：{e}")
