from pathlib import Path

import streamlit as st

from utils import profile
from utils.style import card, hero_emoji

# ── 1. 잡담은 무엇인가 (주제) ─────────────────────────────────
LOGO = Path(__file__).resolve().parent.parent / "assets" / "logo.png"

with card("intro-hero", "white"):
    pic, msg = st.columns([1.25, 2], vertical_alignment="center", gap="medium")
    with pic:
        if LOGO.exists():
            st.image(str(LOGO), width="stretch")
        else:
            hero_emoji("💬")
    with msg:
        st.caption("2026 대한민국 청년 CAREER FAIR AI 해커톤")
        st.markdown("## 잡담(Job談) · 일(Job)에 대한 이야기(談)")
        st.markdown(
            "**공공데이터로 말하는 현직자 AI 선배와 '3년 뒤의 나'가 청년의 진로 고민을 함께 풀어 주는 서비스**예요. "
            "검색 결과 목록 대신 대화로, 추측 대신 고용24·KOSIS 같은 공식 숫자로, 한 사람의 말 대신 여러 관점으로 진로를 비교해 봐요."
        )

# ── 시작 버튼: 제목 박스 바로 아래 ────────────────────────────
st.space("small")
_done = profile.get() is not None
with st.container(key="cta-start", horizontal=True, vertical_alignment="center"):
    with st.container():
        if _done:
            st.markdown("#### ✅ 직무 간이검사를 마쳤어요. 이제 직무 패널에서 직업을 골라 보세요")
            st.caption("간이검사 결과가 선배 대답·직무 적합도·3년 뒤의 나에 이어져요.")
        else:
            st.markdown("#### 🧭 1단계 · 직무 간이검사부터 시작해요 (3분)")
            st.caption("12문항으로 흥미·가치관·강점을 고르면, 이후 모든 대화와 추천이 나에게 맞춰져요.")
    if _done:
        if st.button("직무 패널로 가기", icon=":material/arrow_forward:", key="cta-start-go"):
            st.switch_page("app_pages/panel.py")
    elif st.button("간이검사 시작하기", icon=":material/arrow_forward:", key="cta-start-go"):
        st.switch_page("app_pages/profile.py")

# ── 3. 서비스 안내 (진행 순서) ────────────────────────────────
st.space("small")
st.subheader("이렇게 이용해요", anchor=False)
done = profile.get() is not None
steps = [
    ("1", "직무 간이검사", "가장 먼저 해 주세요! 12문항으로 흥미·가치관·강점을 고르면 이후 대화와 추천이 나에게 맞춰져요.",
     "app_pages/profile.py", "간이검사 시작하기", ":material/person_search:"),
    ("2", "직무 패널", "학과·직업 목록·AI 시대 새 직업에서 직무를 고르고, 그 직무 현직 선배 AI에게 연봉·일과·준비 방법을 물어요.",
     "app_pages/panel.py", "직무 고르러 가기", ":material/groups:"),
    ("3", "3년 뒤의 나", "고른 직무로 취업·대학원·창업 갈림길을 공식 통계로 비교하고, 그 길을 걸은 미래의 나와 대화해요.",
     "app_pages/future.py", "3년 뒤의 나 만나기", ":material/timeline:"),
    ("4", "커리어 로드맵", "3년 뒤의 나와 대화한 길로, 지금부터 3년 뒤까지 할 일·자격·국비 교육을 길 위의 이정표로 그려 줘요.",
     "app_pages/roadmap.py", "로드맵 그리기", ":material/route:"),
]
cols = st.columns(4, gap="small")
for col, (num, title, desc, target, cta, icon) in zip(cols, steps):
    first = num == "1"
    with card(f"step-{num}", "white", parent=col):
        st.html(f'<div class="jd-opt-head"><span class="jd-opt-num">{num}</span>'
                f'<span class="jd-opt-title" style="font-size:1.15rem">{title}</span></div>')
        if first:
            st.badge("완료" if done else "가장 먼저", icon=":material/check:" if done else ":material/flag:",
                     color="green" if done else "blue")
        st.caption(desc)
        primary = (first and not done) or (num == "2" and done)
        if st.button(cta, key=f"home-go-{num}", icon=icon, type="primary" if primary else "secondary", width="stretch"):
            st.switch_page(target)
