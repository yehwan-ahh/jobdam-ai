import streamlit as st

st.title("프로젝트 소개", anchor=False)
st.caption("2026 대한민국 청년 CAREER FAIR AI 해커톤 출품 프로토타입")

st.markdown(
    "**잡담**(Job談)은 '일(Job)에 대한 이야기(談)'라는 뜻이에요. 진로 정보를 검색 결과가 아니라 "
    "**대화**로 전해서, 청년이 부담 없이 여러 길을 비교해 볼 수 있게 돕는 것이 목표입니다."
)

st.subheader("개발 로드맵")
roadmap = [
    ("완료", "사이트 구성 초안과 시연용 화면", True),
    ("진행 중", "커리어넷·KOSIS Open API 키 신청 및 연동", False),
    ("예정", "LLM 기반 직무 페르소나 답변 생성과 출처 표시", False),
    ("예정", "'3년 뒤의 나' 통계 시각화", False),
    ("예정", "사용성 테스트 후 해커톤 최종 시연", False),
]
for status, task, done in roadmap:
    icon = ":green[:material/check_circle:]" if done else ":material/radio_button_unchecked:"
    st.markdown(f"{icon} **{status}** · {task}")

st.subheader("링크")
with st.container(horizontal=True):
    st.link_button(
        "GitHub 소스 코드",
        "https://github.com/yehwan-ahh/jobdam-ai",
        icon=":material/code:",
    )
    st.link_button(
        "커리어넷",
        "https://www.career.go.kr",
        icon=":material/open_in_new:",
    )
    st.link_button(
        "KOSIS 국가통계포털",
        "https://kosis.kr",
        icon=":material/open_in_new:",
    )
