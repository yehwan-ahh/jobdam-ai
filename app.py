import streamlit as st

st.set_page_config(page_title="잡담 | 청년 진로 탐색 AI", page_icon="💬", layout="centered")

st.title("💬 잡담 (Job談)")
st.subheader("현직자 AI 패널과 '3년 뒤의 나'가 함께 고민해 주는 진로 탐색 에이전트")

st.info("2026 대한민국 청년 CAREER FAIR AI 해커톤 출품용 프로토타입입니다. 현재 개발 중이에요.")

tab1, tab2 = st.tabs(["① 직무 패널", "② 3년 뒤의 나"])

with tab1:
    st.markdown(
        "관심 분야를 입력하면 직무별 AI 페르소나가 패널로 등장해 "
        "공공 직업정보를 근거로 업무, 연봉, 필요 역량, 전망을 이야기합니다."
    )
    st.text_input("관심 분야", placeholder="예: 게임 개발", disabled=True)
    st.caption("준비 중")

with tab2:
    st.markdown(
        "취업, 대학원, 창업 같은 갈림길을 고르면 선택지별 '3년 뒤의 나'가 "
        "공식 통계를 바탕으로 장단점을 이야기합니다."
    )
    st.radio("갈림길", ["취업/이직", "대학원 진학", "창업"], disabled=True, horizontal=True)
    st.caption("준비 중")

st.divider()
st.markdown("#### 데이터 출처")
st.markdown(
    "- 한국직업능력연구원 커리어넷 직업정보 (공공누리 제1유형)\n"
    "- 국가데이터처 국가통계포털(KOSIS)\n"
    "\n모든 답변에는 근거 출처를 함께 표시하며, 데이터로 확인할 수 없는 내용은 추정임을 밝힙니다. "
    "실제 개인정보는 입력하거나 저장하지 않습니다."
)
