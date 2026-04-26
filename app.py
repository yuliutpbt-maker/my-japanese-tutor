import streamlit as st
import json

# --- 1. 強效發音組件 (確保重複點擊有效) ---
def play_audio(text):
    js_code = f"""
    <script>
        (function() {{
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance('{text}');
            msg.lang = 'ja-JP';
            msg.rate = 0.85;
            setTimeout(function() {{
                window.speechSynthesis.speak(msg);
            }}, 50);
        }})();
    </script>
    """
    st.components.v1.html(js_code, height=0)

st.title("📖 日文教材練習 (GitHub JSON 版)")

# --- 2. 讀取 GitHub 上的 lessons.json ---
# 這裡維持你原本讀取檔案的邏輯
try:
    with open('lessons.json', 'r', encoding='utf-8') as f:
        lessons_data = json.load(f)
    
    # 讓使用者選擇要練習哪個 Lesson
    lesson_names = list(lessons_data.keys())
    selected_lesson = st.selectbox("請選擇教材章節：", lesson_names)
    
    # 取得該章節的句子清單
    sentences = lessons_data[selected_lesson]

    st.write(f"### 目前進度：{selected_lesson}")
    st.divider()

    # --- 3. 逐句顯示與播放 (優化版) ---
    for i, s in enumerate(sentences):
        with st.container():
            col1, col2 = st.columns([5, 1])
            with col1:
                # 解決字體太小問題，清楚顯示長句子
                st.markdown(f"#### {i+1}. {s}")
            with col2:
                if st.button(f"🔈 播放", key=f"btn_{selected_lesson}_{i}"):
                    play_audio(s)
            st.write("") 

except FileNotFoundError:
    st.error("找不到 lessons.json 檔案，請確認檔案已上傳至 GitHub 倉庫。")
except Exception as e:
    st.error(f"讀取教材時發生錯誤：{e}")

st.divider()
st.caption("提示：若手機沒聲音，請先確認「靜音模式（紅鈴鐺）」已關閉，並點擊按鈕來啟動聲音。")
