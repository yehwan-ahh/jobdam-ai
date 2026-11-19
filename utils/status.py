"""사이드바 연결 상태 배지. 키 값은 절대 보여 주지 않습니다."""

import streamlit as st

from utils import careernet, kosis, llm, worknet


def render_sidebar_status() -> None:
    with st.sidebar:
        st.markdown("**연결 상태**")
        source = llm.key_source()
        if source == "team":
            st.badge(f"AI 연결: 팀 키 ✅ ({llm.provider_label()} · {llm.model()})", color="green")
        elif source == "byok":
            st.badge(f"AI 연결: 내 키 ✅ ({llm.provider_label()} · {llm.model()})", color="green")
        else:
            st.badge("AI 연결: 시연 모드", color="gray")
        st.badge("커리어넷: 연결됨 ✅" if careernet.is_enabled() else "커리어넷: 키 대기 중", color="green" if careernet.is_enabled() else "gray")
        st.badge("KOSIS: 연결됨 ✅" if kosis.is_enabled() else "KOSIS: 키 대기 중", color="green" if kosis.is_enabled() else "gray")
        st.badge("워크넷: 키 입력됨 ✅" if worknet.is_enabled() else "워크넷: 키 대기 중", color="green" if worknet.is_enabled() else "gray")
    llm.render_byok_sidebar()
