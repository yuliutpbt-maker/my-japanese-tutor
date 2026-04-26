import streamlit as st
import json
import os

# --- 1. 強效發音組件 (解決重複點擊與手機鎖定) ---
def play_audio(text):
    # 加入 cancel() 與 50ms 延遲，確保每次點擊都能重新觸發發聲
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

st.title("📖 日文教材練習系統")
st.caption("同步 GitHub lessons/ 資料夾內容")

# --- 2. 讀取 lessons/ 資料夾邏輯 ---
lesson_folder = "lessons"

if os.path.exists(lesson_folder):
    # 抓取資料夾內所有 .json 檔
    json_files = [f for f in os.listdir(lesson_folder) if f.endswith('.json')]
    
    if json_files:
        selected_file = st.selectbox("選擇教材章節：", json_files)
        
        # 讀取選中的 JSON 檔案
        file_path = os.path.join(lesson_folder, selected_file)
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # 假設 JSON 結構是：{"title": "...", "sentences": ["...", "..."]}
            # 或者直接是一個 list。我們這裡相容兩種情況：
            sentences = data.get("sentences", data) if isinstance(data, dict) else data

            st.write(f"### 目前章節：{selected_file.replace('.json', '')}")
            st.divider()

            # --- 3. 逐句顯示 (大字體、防消失、重複播放) ---
            for i, s in enumerate(sentences):
                with st.container():
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        # 使用 H4 級別大字體，方便看著字練習
                        st.markdown(f"#### {i+1}. {s}")
                    with col2:
                        # 確保每個按鈕有唯一的 key
                        if st.button(f"🔈 播放", key=f"btn_{selected_file}_{i}"):
                            play_audio(s)
                    st.write("") # 增加句子間的間距
    else:
        st.warning("lessons/ 資料夾內沒有 JSON 檔案。")
else:
    st.error(f"找不到 '{lesson_folder}' 資料夾，請確認 GitHub 結構正確。")

st.divider()
st.info("提示：若手機無聲，請確認控制中心『紅鈴鐺』已關閉。點擊播放鍵後，手機瀏覽器即可解鎖聲音通道。")
