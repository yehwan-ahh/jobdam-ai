import streamlit as st

from utils import hot_reload

hot_reload.reload_if_changed()  # 새 배포의 utils 변경을 재시작 없이 반영

from utils import profile  # noqa: E402
from utils.status import render_status  # noqa: E402
from utils.style import apply_style  # noqa: E402

st.set_page_config(
    page_title="잡담 | 청년 진로 탐색 AI",
    page_icon=":material/forum:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "visited" not in st.session_state:
    st.session_state.visited = set()

PAGES = {
    "final": st.Page("app_pages/final_design.py", title="잡담 최종 디자인", default=True),
    "home": st.Page("app_pages/home.py", title="시작", icon=":material/home:"),
    "profile": st.Page("app_pages/profile.py", title="현재의 나", icon=":material/person_search:"),
    "panel": st.Page("app_pages/panel.py", title="직무 탐색", icon=":material/groups:"),
    "future": st.Page("app_pages/future.py", title="3년 뒤의 나", icon=":material/timeline:"),
    "roadmap": st.Page("app_pages/roadmap.py", title="커리어 로드맵", icon=":material/route:"),
    "data": st.Page("app_pages/data.py", title="데이터와 원칙", icon=":material/verified:"),
    "about": st.Page("app_pages/about.py", title="프로젝트 소개", icon=":material/info:"),
}
# 메뉴는 아래에서 직접 그려요(위쪽 4단계 진행 메뉴). 기본 메뉴는 숨김.
page = st.navigation(list(PAGES.values()), position="hidden")

if page is PAGES["final"]:
    page.run()
    hot_reload.remember()
    st.stop()

st.session_state.visited.add(page.url_path or "home")
apply_style()

# ── 위쪽 4단계 진행 메뉴: 현재의 나 → 직무 탐색 → 3년 뒤의 나 → 커리어 로드맵 ──────────
S = st.session_state
done = {
    "profile": profile.get() is not None,
    "panel": bool(S.get("selected_job")),
    "future": bool(S.get("chosen_path")),
    "roadmap": bool(S.get("roadmap")),
}
current = next((k for k, p in PAGES.items() if p.url_path == page.url_path), "home")
with st.container(key="topbar", horizontal=True, vertical_alignment="center"):
    with st.container(key="nav-brand", width="content"):
        st.page_link(PAGES["home"], label="잡담 Job談")
    st.space("stretch")
    with st.container(key="nav-steps", horizontal=True, width="content", vertical_alignment="center"):
        for i, k in enumerate(["profile", "panel", "future", "roadmap"]):
            if i:
                st.html('<div class="jd-nav-rule"></div>', width="content")
            state = "now" if k == current else ("done" if done[k] else "todo")
            with st.container(key=f"navstep-{k}-{state}", width="content"):
                st.page_link(PAGES[k], label=PAGES[k].title)
    with st.container(key="nav-more", width="content"):
        with st.popover("", icon=":material/more_horiz:", help="연결 상태 · 내 API 키 · 안내"):
            st.page_link(PAGES["final"], label="최종 디자인", icon=":material/auto_awesome:")
            st.page_link(PAGES["data"], label="데이터와 원칙", icon=":material/verified:")
            st.page_link(PAGES["about"], label="프로젝트 소개", icon=":material/info:")
            st.divider()
            render_status()

from utils import company  # noqa: E402

company.warm()  # 회사 목록(강소기업·DART)을 뒤에서 미리 받아 둬요

page.run()
hot_reload.remember()

if current != "home":
    st.space("medium")
    st.caption(
        "잡담(Job談) · 2026 대한민국 청년 CAREER FAIR AI 해커톤 출품 프로토타입 · "
        "데이터 출처: 고용24(한국고용정보원), 국가데이터처 KOSIS, 한국고용정보원 상위진출직업, 한국직업능력연구원 커리어넷, "
        "DART(금융감독원), 국민연금공단, 한국산업인력공단 Q-Net"
    )
