import streamlit as st

from utils.style import card, hero_emoji

st.title("프로젝트 소개 💬", anchor=False)
st.caption("2026 대한민국 청년 CAREER FAIR AI 해커톤 출품 프로토타입")

st.space("small")
with card("intro", "sky"):
    pic, msg = st.columns([1, 5], vertical_alignment="center")
    with pic:
        hero_emoji("💬")
    with msg:
        st.markdown("### 잡담(Job談), 일에 대한 이야기")
        st.markdown(
            "진로 정보를 검색 결과가 아니라 **대화**로 전해서, "
            "청년이 부담 없이 여러 길을 비교해 볼 수 있게 돕는 것이 목표예요."
        )

st.space("small")
left, right = st.columns([3, 2], gap="medium")
with card("roadmap", "white", parent=left):
    st.markdown("#### 개발 로드맵")
    roadmap = [
        ("사이트 구성 초안과 시연용 화면", "완료", "green"),
        ("고용24 직업정보·훈련과정, 커리어넷, KOSIS 연동", "완료", "green"),
        ("직무 선배 AI 대화·답변 출처 표시·개인정보 차단", "완료", "green"),
        ("'3년 뒤의 나' 통계 시각화", "진행 중", "blue"),
        ("사용성 테스트 후 해커톤 최종 시연", "예정", "gray"),
    ]
    for task, status, color in roadmap:
        with st.container(horizontal=True, vertical_alignment="center", horizontal_alignment="distribute"):
            st.markdown(task)
            st.badge(status, color=color)  # type: ignore[arg-type]

with card("links", "mint", parent=right):
    st.markdown("#### 링크")
    st.link_button("GitHub 소스 코드", "https://github.com/yehwan-ahh/jobdam-ai", icon=":material/code:", width="stretch")
    st.link_button("커리어넷", "https://www.career.go.kr", icon=":material/open_in_new:", width="stretch")
    st.link_button("KOSIS 국가통계포털", "https://kosis.kr", icon=":material/open_in_new:", width="stretch")
