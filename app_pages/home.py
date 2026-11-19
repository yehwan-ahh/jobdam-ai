import streamlit as st

from utils.demo_data import FUTURES, PANELS
from utils.style import big_number, card, hero_emoji, icon_tile

# ── 헤더 ──────────────────────────────────────────────
head_l, head_r = st.columns([3, 2], vertical_alignment="center")
with head_l:
    st.title("대시보드 👋", anchor=False)
    st.caption("반가워요! 오늘은 어떤 진로 고민을 나눠 볼까요?")
with head_r:
    with st.container(horizontal=True, horizontal_alignment="right"):
        st.badge("공공데이터 근거", icon=":material/verified:", color="green")
        st.badge("개인정보 미수집", icon=":material/lock:", color="blue")

st.space("small")

# ── 1행: 인사 카드 + 숫자 카드 3개 ──────────────────────
hero, s1, s2, s3 = st.columns([2.2, 1, 1, 1], gap="medium")

with card("hero", "peach", parent=hero):
    pic, msg = st.columns([1, 1.4], vertical_alignment="center")
    with pic:
        hero_emoji("🧑‍🎓")
    with msg:
        st.markdown("### 좋은 하루예요! ☀️")
        st.markdown("현직자 AI 패널과 **3년 뒤의 나**가 함께 고민해 드릴게요.")
        st.page_link("app_pages/panel.py", label="패널 만나러 가기", icon=":material/arrow_forward:")

persona_count = sum(len(v) for v in PANELS.values())
stats = [
    (s1, "sky", "navy", "💼", "탐색할 수 있는 분야", f"{len(PANELS)}개", "시연 모드 기준"),
    (s2, "peach", "peach", "🧑‍💻", "직무 페르소나", f"{persona_count}명", "분야별 3명씩"),
    (s3, "mint", "teal", "🧭", "갈림길 시나리오", f"{len(FUTURES)}개", "취업·대학원·창업"),
]
for col, color, tone, emoji, label, value, note in stats:
    with card(f"stat-{tone}", color, parent=col):
        st.markdown(f"**{label}**")
        icon_tile(emoji, f"stat-{tone}", tone)
        big_number(value)
        st.caption(note)

st.space("small")

# ── 2행: 두 가지 기능 + 탐색 체크리스트 ─────────────────
feat, tasks = st.columns([2, 1.3], gap="medium")

with feat:
    f1, f2 = st.columns(2, gap="medium")
    with card("feat-panel", "white", parent=f1):
        icon_tile("👥", "feat-panel", "navy")
        st.markdown("#### 직무 패널")
        st.caption(
            "관심 분야를 고르면 직무별 AI 페르소나가 패널 토크처럼 등장해 "
            "업무, 필요 역량, 전망을 이야기해요."
        )
        st.page_link("app_pages/panel.py", label="패널 열기", icon=":material/arrow_forward:")
    with card("feat-future", "white", parent=f2):
        icon_tile("🔭", "feat-future", "teal")
        st.markdown("#### 3년 뒤의 나")
        st.caption(
            "취업, 대학원, 창업 중 갈림길을 고르면 그 길을 걸은 '3년 뒤의 나'가 "
            "좋았던 점과 아쉬웠던 점을 들려줘요."
        )
        st.page_link("app_pages/future.py", label="미래의 나 만나기", icon=":material/arrow_forward:")

    with card("how", "white"):
        st.markdown("#### 이렇게 작동해요")
        steps = st.columns(4)
        flow = [
            ("✏️", "고민 입력", "개인정보 없이 분야·갈림길만 골라요"),
            ("🔎", "근거 찾기", "커리어넷·KOSIS 데이터 검색"),
            ("💬", "페르소나 대화", "근거를 바탕으로 대화체 설명"),
            ("📎", "출처 표시", "추정은 추정이라고 밝혀요"),
        ]
        for col, (emoji, title, desc) in zip(steps, flow):
            with col:
                st.markdown(f"**{emoji} {title}**")
                st.caption(desc)

visited: set[str] = st.session_state.get("visited", set())
checklist = [
    ("🎯", "관심 분야 골라 패널 보기", "panel", "app_pages/panel.py"),
    ("🔭", "3년 뒤의 나 만나기", "future", "app_pages/future.py"),
    ("📎", "데이터 출처 확인하기", "data", "app_pages/data.py"),
]
done = sum(1 for _, _, path, _ in checklist if path in visited)

with card("tasks", "white", parent=tasks):
    st.markdown("#### 오늘의 탐색 체크리스트")
    for emoji, label, path, target in checklist:
        row = st.container(horizontal=True, vertical_alignment="center")
        with row:
            st.page_link(target, label=f"{emoji} {label}")
            if path in visited:
                st.badge("완료", icon=":material/check:", color="green")
            else:
                st.badge("시작 전", color="gray")
    st.space("small")
    st.markdown(f"**진행률 {done}/{len(checklist)}**")
    st.progress(done / len(checklist))

    st.space("small")
    with card("remind", "sky"):
        st.markdown("**잊지 마세요! 🔒**")
        st.caption("실명, 연락처 같은 개인정보는 입력하지 않아도 돼요.")

st.space("small")

# ── 3행: 응원 카드 ─────────────────────────────────────
with card("cheer", "cream"):
    c_l, c_r = st.columns([1, 5], vertical_alignment="center")
    with c_l:
        hero_emoji("☁️")
    with c_r:
        st.markdown("### 고민하고 있다는 것 자체가 시작이에요")
        st.markdown("정답을 찾기보다, 여러 길을 비교해 보는 것부터 함께해요.")
