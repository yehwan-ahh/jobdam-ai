"""직무 패널: ① 패널에게 이야기 → ② 추천 직무 선택 → ③ 그 직무 선배에게 깊게 묻기."""

import streamlit as st

from utils import interviews, llm, majors, training
from utils.demo_data import DEMO_NOTICE, PANELS
from utils.evidence import job_evidence, recommend_candidates, show_sources
from utils.prompts import answer_mode, find_personal_info, job_system, recommend_system
from utils.style import card

# ── 상태 ─────────────────────────────────────────────────────
S = st.session_state
S.setdefault("panel_explore", [])  # 1단계 대화 [{role, content}]
S.setdefault("panel_recs", [])  # 추천 [{name, why, basis}]
S.setdefault("selected_job", None)  # 선택한 직무 {name, why, basis}
S.setdefault("panel_job_chats", {})  # 직무별 대화
S.setdefault("my_major", None)  # 고른 학과(위젯이 사라져도 유지)


def choose(job: dict) -> None:
    S.selected_job = job


def back_to_explore() -> None:
    S.selected_job = None


def blocked_by_pii(text: str) -> bool:
    pii = find_personal_info(text)
    if pii:
        with st.chat_message("assistant"):
            st.warning(
                f"{', '.join(pii)}처럼 보이는 정보가 있어서 AI에 보내지 않았어요. 그 부분을 빼고 다시 말해 주세요.",
                icon=":material/lock:",
            )
    return bool(pii)


st.title("직무 패널 👥", anchor=False)
step = 3 if S.selected_job else (2 if S.panel_recs else 1)
with st.container(horizontal=True):
    for n, label in ((1, "패널에게 이야기"), (2, "추천 직무 선택"), (3, "직무 선배에게 묻기")):
        st.badge(f"{n}. {label}", color="blue" if n == step else "gray", icon=":material/check:" if n < step else None)

if not llm.is_enabled():
    st.info(DEMO_NOTICE, title="시연 모드", icon=":material/science:")

# ════════════════════════════════════════════════════════════
# ③ 선택한 직무에 대해 깊게 묻기
# ════════════════════════════════════════════════════════════
if S.selected_job:
    job = S.selected_job
    name = job["name"]
    st.space("small")
    with card("job-head", "sky"):
        st.badge("선택한 직무", icon=":material/work:", color="blue")
        st.markdown(f"### {name}")
        if job.get("why"):
            st.markdown(job["why"])
        if job.get("basis"):
            st.caption(f":material/link: 추천 근거: {job['basis']}")
        with st.container(horizontal=True):
            st.button("다른 직무 보기", icon=":material/arrow_back:", on_click=back_to_explore)
            if st.button("이 직무로 '3년 뒤의 나' 보기", icon=":material/timeline:", type="primary"):
                st.switch_page("app_pages/future.py")

    if training.is_enabled():
        st.space("small")
        with card("job-training", "white"):
            training.render(name)

    st.space("small")
    st.subheader(f"{name} 선배에게 물어보기", anchor=False)
    st.caption("하루 일과, 준비 방법, 힘든 점, 연봉처럼 궁금한 걸 편하게 물어보세요. 실명·연락처는 적지 말아 주세요.")

    history: list[dict[str, str]] = S.panel_job_chats.setdefault(name, [])
    quick = None
    if not history:
        quick = st.pills(
            "이렇게 물어볼 수 있어요",
            ["하루는 어떻게 보내요?", "지금부터 뭘 준비하면 돼요?", "가장 힘든 점은 뭐예요?", "연봉과 전망은 어때요?"],
            key=f"quick_{name}",
        )
    for msg in history:
        with st.chat_message(msg["role"], avatar="🧑‍💼" if msg["role"] == "assistant" else None):
            st.markdown(msg["content"])

    prompt = st.chat_input(f"{name} 선배에게 궁금한 점을 물어보세요", key="job_input", submit_mode="disable") or quick
    if prompt:
        with st.chat_message("user"):
            st.write(prompt)
        if blocked_by_pii(prompt):
            st.stop()
        history.append({"role": "user", "content": prompt})
        with st.chat_message("assistant", avatar="🧑‍💼"):
            with st.status("공공 직업정보·현직자 인터뷰 찾는 중", type="step") as step_box:
                evidence, sources = job_evidence(name, prompt, S.my_major)
                st.caption("찾은 근거: " + (" · ".join(sources) if sources else "없음 (AI 일반 지식으로 답해요)"))
                step_box.update(label="근거를 찾았어요" if sources else "공공데이터 근거 없음", state="complete")
            if llm.is_enabled():
                with st.spinner("선배가 답변을 준비하고 있어요"):
                    result = llm.generate(job_system(name, evidence), history[-10:])
                if not result.text:
                    st.warning(result.error or "답변을 만들지 못했어요.", icon=":material/error:")
                    history.pop()
                    st.stop()
                reply = result.text
                st.markdown(reply)
                show_sources(sources)
                st.caption(
                    f"AI 답변 · {llm.provider_label()} · 숫자는 공공데이터 출처가 있을 때만, "
                    "'(일반적인 경향)'은 AI 일반 지식이에요."
                )
            else:
                reply = f"지금은 시연 모드예요. AI 키가 연결되면 '{name}' 선배가 공공데이터와 현직자 인터뷰를 바탕으로 답해 드려요."
                st.write(reply)
        history.append({"role": "assistant", "content": reply})
    st.stop()

# ════════════════════════════════════════════════════════════
# ① 패널에게 이야기 → ② 추천 직무 선택
# ════════════════════════════════════════════════════════════
st.caption(
    "전공, 관심사, 고민을 편하게 말하면 패널이 살펴볼 만한 직무를 추천해요. "
    "마음에 드는 직무를 고르면 그 직무 선배와 깊게 이야기할 수 있어요."
)

my_major = majors.render_picker("panel")
S.my_major = my_major

with st.chat_message("assistant", avatar="🎤"):
    st.markdown(
        "**패널 사회자**: 반가워요! 요즘 어떤 진로 고민이 있나요? "
        "좋아하는 것, 전공, 해 보고 싶은 일 무엇이든 좋아요."
    )
for msg in S.panel_explore:
    with st.chat_message(msg["role"], avatar="🎤" if msg["role"] == "assistant" else None):
        st.markdown(msg["content"])

examples = {
    "게임을 좋아하는데 어떤 직업이 있을까요?": "게임을 좋아하는데 어떤 직업이 있을까요?",
    "사람을 돕는 일을 하고 싶어요": "사람을 돕는 일을 하고 싶어요",
    "데이터 쪽으로 가고 싶은데 비전공자예요": "데이터 쪽으로 가고 싶은데 비전공자예요",
    "내 학과 졸업자는 어디로 갈까?": (
        f"저는 {my_major}를 전공하고 있어요. 제 학과 졸업자가 많이 가는 직업 중에 추천해 주세요."
        if my_major
        else "제 학과 졸업자가 어디로 가는지 궁금해요."
    ),
}
picked_example = None
if not S.panel_explore:
    picked_example = st.pills("이렇게 시작해 보세요", list(examples), key="panel_examples", label_visibility="collapsed")

prompt = st.chat_input("패널에게 진로 고민을 이야기해 보세요", key="explore_input", submit_mode="disable")
if picked_example and not prompt:
    prompt = examples[picked_example]

if prompt:
    with st.chat_message("user"):
        st.write(prompt)
    if not blocked_by_pii(prompt):
        S.panel_explore.append({"role": "user", "content": prompt})
        candidates = recommend_candidates(my_major)
        with st.chat_message("assistant", avatar="🎤"):
            if llm.is_enabled():
                with st.spinner("패널이 어울리는 직무를 고르고 있어요"):
                    data, err = llm.generate_json(
                        recommend_system(candidates, majors.evidence(my_major)), S.panel_explore[-8:]
                    )
                if data is None:
                    st.warning(err or "추천을 만들지 못했어요.", icon=":material/error:")
                    S.panel_explore.pop()
                    st.stop()
                message = str(data.get("message", "")).strip() or "이야기 잘 들었어요. 이런 직무를 살펴보면 좋겠어요."
                recs = [
                    {
                        "name": str(j.get("name", "")).strip(),
                        "why": str(j.get("why", "")).strip(),
                        "basis": str(j.get("basis", "")).strip(),
                    }
                    for j in data.get("jobs", [])
                    if isinstance(j, dict) and j.get("name")
                ][:4]
            else:
                pool = majors.top_jobs(my_major) if my_major else [p["role"] for p in PANELS["게임 개발"]]
                message = "지금은 시연 모드라 예시로 추천해 드릴게요."
                recs = [{"name": n, "why": "", "basis": majors.SOURCE if my_major else "잡담 예시 패널"} for n in pool[:4]]
            st.markdown(message)
        S.panel_explore.append({"role": "assistant", "content": message})
        if recs:
            S.panel_recs = recs
        st.rerun()

# ② 추천 직무 카드
if S.panel_recs:
    st.space("small")
    st.subheader("패널이 추천한 직무", anchor=False)
    cols = st.columns(len(S.panel_recs), gap="medium")
    tones = ["sky", "mint", "peach", "cream"]
    for i, (col, rec) in enumerate(zip(cols, S.panel_recs)):
        with card(f"rec-{i}", tones[i % len(tones)], parent=col):
            st.markdown(f"#### {rec['name']}")
            if rec.get("why"):
                st.write(rec["why"])
            if rec.get("basis"):
                st.caption(f":material/link: {rec['basis']}")
            if interviews.is_enabled() and rec["name"] in interviews.jobs():
                st.badge("현직자 인터뷰 있음", icon=":material/mic:", color="green")
            st.button(
                "이 직무 선배에게 묻기",
                key=f"pick_{i}",
                icon=":material/arrow_forward:",
                type="primary",
                width="stretch",
                on_click=choose,
                args=(rec,),
            )

st.space("small")
with st.expander("직접 고르기", icon=":material/search:"):
    direct = st.selectbox(
        "직무 이름",
        recommend_candidates(my_major),
        index=None,
        placeholder="목록에서 고르거나 직무 이름을 입력하세요",
        accept_new_options=True,
        key="direct_job",
    )
    st.button(
        "이 직무로 이야기하기",
        disabled=not direct,
        on_click=choose,
        args=({"name": direct or "", "why": "", "basis": "직접 선택"},),
        icon=":material/arrow_forward:",
    )

st.caption(f"답변 모드: {'균형(공공데이터 + AI 일반 지식)' if answer_mode() == 'balanced' else '근거 우선'}")
