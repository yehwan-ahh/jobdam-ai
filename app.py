import streamlit as st

from utils import hot_reload

hot_reload.reload_if_changed()  # 새 배포의 utils 변경을 재시작 없이 반영

from utils.status import render_sidebar_status  # noqa: E402
from utils.style import apply_style, card  # noqa: E402

st.set_page_config(
    page_title="잡담 | 청년 진로 탐색 AI",
    page_icon=":material/forum:",
    layout="wide",
)

if "visited" not in st.session_state:
    st.session_state.visited = set()

page = st.navigation(
    {
        "잡담 Job談": [
            st.Page(
                "app_pages/home.py",
                title="대시보드",
                icon=":material/space_dashboard:",
                default=True,
                help="오늘의 진로 탐색 현황과 바로가기를 한눈에 보는 홈 대시보드입니다.",
            ),
            st.Page(
                "app_pages/profile.py",
                title="직무 간이검사",
                icon=":material/person_search:",
                help="가장 먼저 해 주세요. 흥미·가치관·강점을 고르면 대화와 직무 적합도가 나에게 맞춰져요.",
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
                "app_pages/roadmap.py",
                title="커리어 로드맵",
                icon=":material/route:",
                help="직무와 갈림길을 고르면 지금부터 3년 뒤까지의 길을 이정표로 그려 줍니다.",
            ),
        ],
        "안내": [
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
    },
    position="sidebar",
)

st.session_state.visited.add(page.url_path or "home")
apply_style()

render_sidebar_status()

with st.sidebar:
    st.space("medium")
    with card("sidebar", "white"):
        st.markdown("### 🪴")
        st.markdown("**오늘도 한 걸음**")
        st.caption("진로 고민은 천천히, 함께 나눠도 괜찮아요.")

page.run()
hot_reload.remember()

st.space("medium")
st.caption(
    "잡담(Job談) · 2026 대한민국 청년 CAREER FAIR AI 해커톤 출품 프로토타입 · "
    "데이터 출처: 고용24(한국고용정보원), 국가데이터처 KOSIS, 한국고용정보원 상위진출직업, 한국직업능력연구원 커리어넷"
)
