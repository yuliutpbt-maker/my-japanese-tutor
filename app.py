import streamlit as st

st.set_page_config(page_title="日文文章練習板", layout="wide")

# --- 1. 穩定的發聲函數 (使用 JavaScript 朗讀) ---
def play_audio(text):
    # 這是目前在電腦版最穩定的方案
    js_code = f"""
    <script>
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance('{text}');
        msg.lang = 'ja-JP';
        msg.rate = 0.85; // 稍微放慢一點點，讓你聽得更清楚
        window.speechSynthesis.speak(msg);
    </script>
    """
    st.components.v1.html(js_code, height=0)

st.title("📖 日文文章朗讀練習")
st.caption("看著文字、聽發音、開口練，不受判定功能干擾")

# --- 2. 文章內容區域 (你可以隨時更換這裡的文字) ---
article_title = "最近的近況與計畫"
article_content = """最近は仕事が忙しくて、ゆっくり休む時間がなくて困っています。
来週からは少し余裕ができるはずなので、友達と旅行に行く計画を立てています。
新しい場所に行って、美味しいものをたくさん食べたいです。"""

# 將文章拆成句子顯示
sentences = [s.strip() for s in article_content.split('\n') if s.strip()]

st.subheader(f"文章：{article_title}")

# --- 3. 逐句練習區 ---
for i, s in enumerate(sentences):
    # 建立一個清晰的區塊顯示每一句
    with st.container():
        col1, col2 = st.columns([4, 1])
        with col1:
            # 讓字體大一點，解決 Gemini Live 看不到長句的問題
            st.markdown(f"#### {i+1}. {s}")
        with col2:
            if st.button(f"🔈 聽發音", key=f"btn_{i}"):
                play_audio(s)
        st.divider()

# --- 4. 自由練習區 ---
st.write("---")
custom_text = st.text_area("也可以貼上你想練習的其他句子：", height=100)
if st.button("🔈 朗讀上方自訂文字"):
    if custom_text:
        play_audio(custom_text)
