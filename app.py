# --- 5. 介面設計 (修正點擊句子沒聲音的問題) ---
    st.subheader("📖 全文預覽")
    
    full_text_container = st.container()
    with full_text_container:
        for i, s in enumerate(sentences):
            # 點擊即切換並發聲
            if st.button(s, key=f"list_btn_{i}", type="primary" if i == idx else "secondary", use_container_width=True):
                # 關鍵修正：先呼叫播放
                play_audio(s)
                
                # 更新索引
                st.session_state.idx = i
                
                # 稍微延遲一下下再重整，確保 JS 指令已經發出
                import time
                time.sleep(0.1) 
                st.rerun()
