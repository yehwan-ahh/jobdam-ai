"""연결 상태 배지. 키 값은 절대 보여 주지 않습니다."""

import streamlit as st

from utils import careernet, kosis, llm, training, worknet


def render_status() -> None:
    """현재 컨테이너(위쪽 메뉴의 '더보기')에 연결 상태와 '내 API 키 쓰기'를 그려요."""
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
    st.badge("고용24 직업정보: 연결됨 ✅" if worknet.is_enabled() else "고용24 직업정보: 키 대기 중", color="green" if worknet.is_enabled() else "gray")
    st.badge("고용24 훈련과정: 연결됨 ✅" if training.is_enabled() else "고용24 훈련과정: 키 대기 중", color="green" if training.is_enabled() else "gray")
    st.divider()
    st.markdown("**내 API 키 쓰기**")
    llm.render_byok_body()


def render_sidebar_status() -> None:  # 예전 이름 호환
    with st.sidebar.expander("연결 상태", icon=":material/link:", expanded=False):
        render_status()
