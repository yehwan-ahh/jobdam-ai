import streamlit as st

st.set_page_config(
    page_title="잡담 | 청년 진로 탐색 AI",
    page_icon=":material/forum:",
    layout="wide",
)

page = st.navigation(
    [
        st.Page(
            "app_pages/home.py",
            title="홈",
            icon=":material/home:",
            default=True,
            help="잡담이 무엇인지, 어떤 고민을 어떻게 도와주는지 한눈에 보는 소개 페이지입니다.",
        ),
        st.Page(
            "app_pages/panel.py",
            title="직무 패널",
            icon=":material/groups:",
            help="관심 분야를 고르면 직무별 AI 페르소나가 패널로 등장해 업무와 필요 역량을 이야기합니다.",
        ),
        st.Page(
            "app_pages/future.py",
            title="3년 뒤의 나",
            icon=":material/timeline:",
            help="취업·대학원·창업 중 갈림길을 고르면 그 길을 간 '3년 뒤의 나'가 장단점을 들려줍니다.",
        ),
        st.Page(
            "app_pages/data.py",
            title="데이터와 원칙",
            icon=":material/verified:",
            help="잡담이 근거로 쓰는 공공데이터 출처와 개인정보·AI 답변 원칙을 정리했습니다.",
        ),
        st.Page(
            "app_pages/about.py",
            title="프로젝트 소개",
            icon=":material/info:",
            help="해커톤 출품 정보, 개발 로드맵, 소스 코드 링크를 안내합니다.",
        ),
    ],
    position="top",
)

page.run()

st.divider()
st.caption(
    "잡담(Job談) · 2026 대한민국 청년 CAREER FAIR AI 해커톤 출품 프로토타입 · "
    "데이터 출처: 한국직업능력연구원 커리어넷, 국가데이터처 KOSIS"
)
