"""시작 화면: 제목 · 4단계 · 시작 버튼만 있는 깔끔한 첫 화면 (UX/UI 디자인 시안)."""

import streamlit as st

from utils import profile

S = st.session_state
done = [
    profile.get() is not None,
    bool(S.get("selected_job")),
    bool(S.get("chosen_path")),
    bool(S.get("roadmap")),
]
labels = ["현재의 나", "직무 탐색", "3년 뒤의 나", "커리어 로드맵"]
targets = ["app_pages/profile.py", "app_pages/panel.py", "app_pages/future.py", "app_pages/roadmap.py"]
nxt = next((i for i, d in enumerate(done) if not d), 3)
hints = [
    "현재의 나 · 어떤 일에 흥미를 느끼는지, 내 강점은 무엇인지 알아봐요.",
    "직무 탐색 · 관심 직무를 골라 AI 선배에게 일과와 준비 방법을 물어봐요.",
    "3년 뒤의 나 · 취업·대학원·창업 중 한 길을 걸은 미래의 나와 이야기해요.",
    "커리어 로드맵 · 이번 주 첫 행동부터 3년까지의 준비를 정리해요.",
]

steps_html = "".join(
    f'<div class="{"on" if i == nxt else ("done" if done[i] else "")}">{label}</div>' for i, label in enumerate(labels)
)
st.html(
    '<div class="jd-hero">'
    "<h1>수많은 갈림길에서<br>저마다의 빛을 향해.</h1>"
    '<p class="lede">고용24·KOSIS의 공식 데이터와 AI 선배와의 대화로, 나에게 맞는 진로를 설계해 보세요.</p>'
    f'<div class="jd-steps">{steps_html}</div>'
    f'<p class="jd-hero-sub">{hints[nxt]}</p>'
    "</div>"
)
st.space("small")
with st.container(key="hero-start", horizontal=True, horizontal_alignment="center"):
    label = "시작" if nxt == 0 else ("이어서 하기" if not all(done) else "로드맵 보기")
    if st.button(label, icon=":material/arrow_forward:", icon_position="right", key="hero-start-go"):
        st.switch_page(targets[nxt])
st.html(
    f'<p class="jd-hero-sub">{"간이검사 · 12문항 · 약 3분" if nxt == 0 else labels[nxt] + "부터 이어서 해요"}</p>'
)
