"""직무 패널: ① 패널에게 이야기 → ② 추천 직무 선택 → ③ 그 직무 선배에게 깊게 묻기."""

import streamlit as st

from utils import interviews, llm, majors, training, worknet
from utils.demo_data import DEMO_NOTICE, PANELS
from utils.evidence import job_evidence, recommend_candidates
from utils.prompts import answer_mode, find_personal_info, job_system, panel_opinion_system, recommend_system
from utils.style import card, scroll_to_top

# ── 상태 ─────────────────────────────────────────────────────
S = st.session_state
S.setdefault("panel_explore", [])  # 1단계 대화 [{role, content}]
S.setdefault("panel_recs", [])  # 추천 [{name, why, basis}]
S.setdefault("selected_job", None)  # 선택한 직무 {name, why, basis}
S.setdefault("panel_job_chats", {})  # 직무별 대화
S.setdefault("my_major", None)  # 고른 학과(위젯이 사라져도 유지)
S.setdefault("panel_opinions", {})  # 직무별 '다른 선배 한마디' {question, items}


def related_jobs(job: str, n: int = 2) -> list[str]:
    """함께 의견을 들을 관련 직무: 패널 추천 → 고용24 이름이 비슷한 직업 → 같은 학과 상위 진출 직업 → 기본 패널 직무.
    (학과 상위 진출 직업에는 사무직처럼 결이 다른 직업도 섞여 있어 유사 직업을 먼저 봅니다.)"""
    pool: list[str] = [r["name"] for r in S.panel_recs]
    if worknet.is_enabled():
        pool += [j.get("jobNm", "") for j in (worknet.search_jobs(job, limit=5) or [])]
    if S.my_major:
        pool += majors.top_jobs(S.my_major)
    for personas in PANELS.values():
        pool += [p["role"] for p in personas]
    def norm(text: str) -> str:  # '응용 소프트웨어 개발자'와 '응용소프트웨어개발자'를 같은 직무로
        return "".join(ch for ch in text if ch.isalnum())

    me = norm(job)
    picked: list[str] = []
    for cand in pool:
        c = norm(cand)
        if c and me not in c and c not in me and all(norm(p) != c for p in picked):
            picked.append(cand)
        if len(picked) == n:
            break
    return picked


def choose(job: dict) -> None:
    S.selected_job = job
    S.just_chosen = True  # 다음 화면에서 입력창으로 포커스


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


def option_header(num: int, title: str, desc: str) -> None:
    """옵션 카드 머리: 검정 원형 번호 배지 + 굵은 제목 + 한 줄 설명."""
    st.html(
        f'<div class="jd-opt-head"><span class="jd-opt-num">{num}</span>'
        f'<span class="jd-opt-title">{title}</span></div>'
    )
    st.caption(desc)


BR = "  " + chr(10)  # 마크다운 줄바꿈


def parse_answer(data: dict | None) -> tuple[str, list[str]]:
    """AI가 돌려준 JSON에서 대답과 출처 목록을 꺼냅니다. 키 이름이 조금 달라도 받아 줍니다."""
    if not isinstance(data, dict):
        return "", []
    for k in ("answer", "reply", "response", "대답", "답변"):  # {"answer": {"text": ...}} 같은 중첩도 풀어 줍니다
        v = data.get(k)
        if isinstance(v, dict):
            data = {**data, k: next((x for x in v.values() if isinstance(x, str)), "")}
        elif isinstance(v, list) and all(isinstance(x, str) for x in v):
            data = {**data, k: chr(10).join(v)}
    answer = next((data[k] for k in ("answer", "reply", "response", "대답", "답변") if isinstance(data.get(k), str) and data[k].strip()), "")
    if not answer:  # 가장 긴 문자열 값을 대답으로
        strings = [v for v in data.values() if isinstance(v, str)]
        answer = max(strings, key=len) if strings else ""
    raw = next((data[k] for k in ("sources", "source", "출처", "근거") if isinstance(data.get(k), list)), [])
    used = []
    for x in raw:
        if isinstance(x, dict) and (x.get("from") or x.get("source")):
            what = str(x.get("what", "")).strip()
            src = str(x.get("from") or x.get("source")).strip()
            used.append(f"{what}: {src}" if what else src)
        elif isinstance(x, str) and x.strip():
            used.append(x.strip())
    return answer.strip(), used


def render_sources(used: list[str], found: list[str]) -> None:
    """답변 아래 근거 영역: 어떤 내용이 어느 공공데이터에서 왔는지, 나머지는 AI 일반 지식."""
    lines = used or ([f"참고한 자료: {' · '.join(found)}"] if found else [])
    tail = (
        "그 밖의 경험담·조언은 AI가 일반적인 경향을 바탕으로 정리했어요."
        if lines
        else "이번 대답은 공공데이터 근거 없이 AI 일반 지식으로 정리했어요."
    )
    st.caption(BR.join(["**근거**", *[f":material/link: {line}" for line in lines], tail]))


st.title("직무 패널 👥", anchor=False)
if not S.selected_job and not S.panel_explore:
    scroll_to_top()
if not S.selected_job:
    st.markdown("#### 🎤 반가워요! 요즘 어떤 진로 고민이 있나요?")
    st.markdown(
        "궁금한 직무를 고르면 그 직무 현직 선배와 바로 이야기할 수 있어요. "
        "학과로 찾거나, 직접 고르거나, 잘 모르겠다면 아래에서 패널에게 고민을 말해 보세요."
    )
step = 2 if S.selected_job else 1
with st.container(horizontal=True):
    for n, label in ((1, "직무 고르기"), (2, "직무 선배와 대화")):
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

    st.space("small")
    st.subheader(f"{name} 선배와 대화", anchor=False, help="실명·연락처 같은 개인정보는 적지 말아 주세요.")

    history: list[dict[str, str]] = S.panel_job_chats.setdefault(name, [])
    # 선배의 첫 인사 (대화 시작 유도)
    with st.chat_message("assistant", avatar="🧑‍💼"):
        st.markdown(
            f"안녕하세요, **{name}** 일을 하고 있는 선배예요. "
            "하루 일과, 연봉, 준비 방법, 힘든 점… 뭐든 편하게 물어봐요 👇"
        )
    quick = None
    if not history:
        quick = st.pills(
            "이렇게 물어봐도 돼요",
            ["하루는 어떻게 보내요?", "지금부터 뭘 준비하면 돼요?", "가장 힘든 점은 뭐예요?", "연봉과 전망은 어때요?"],
            key=f"quick_{name}",
        )
    for msg in history:
        with st.chat_message(msg["role"], avatar="🧑‍💼" if msg["role"] == "assistant" else None):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and "sources" in msg:
                render_sources(msg["sources"], msg.get("found", []))

    # ── 패널 토론: 같은 질문을 다른 직무 선배 2명에게도 ─────────────
    opinions = S.panel_opinions.get(name)
    if opinions:
        st.markdown(f"**👥 다른 선배들의 한마디** · :gray[“{opinions['question']}”]")
        cols = st.columns(len(opinions["items"]), gap="medium")
        for col, op in zip(cols, opinions["items"]):
            with card(f"op-{op['job']}", "white", parent=col):
                st.markdown(f"##### 🧑‍💼 {op['job']} 선배")
                st.markdown(op["answer"])
                render_sources(op["used"], op["found"])
                st.button(
                    "이 선배와 대화하기",
                    key=f"op-go-{op['job']}",
                    icon=":material/forum:",
                    on_click=choose,
                    args=({"name": op["job"], "why": f"'{name}' 선배와 대화하다가 함께 들어 본 직무예요.", "basis": ""},),
                    width="stretch",
                )
    if llm.is_enabled():
        last_q = next((m["content"] for m in reversed(history) if m["role"] == "user"), None)
        ask_panel = st.button(
            "다른 직무 선배 의견도 듣기",
            icon=":material/groups:",
            help="방금 한 질문(없으면 '이 직무 어때요?')을 관련 직무 선배 2명에게도 물어 나란히 비교해요.",
        )
        if ask_panel:
            question = last_q or "이 직무 어때요?"
            others = related_jobs(name)
            with st.spinner(f"{', '.join(others)} 선배에게도 물어보는 중…"):
                bundles = [job_evidence(o, question, S.my_major) for o in others]
                systems = [
                    panel_opinion_system(o, ev, [name] + [x for x in others if x != o])
                    for o, (ev, _) in zip(others, bundles)
                ]
                results = llm.generate_json_many(systems, [{"role": "user", "content": question}])
            items = []
            for o, (_, found), (data, err) in zip(others, bundles, results):
                answer, used = parse_answer(data)
                if answer:
                    items.append({"job": o, "answer": answer, "used": used, "found": found})
            if items:
                S.panel_opinions[name] = {"question": question, "items": items}
                st.rerun()
            st.warning("다른 선배들의 의견을 받지 못했어요. 잠시 뒤 다시 눌러 주세요.", icon=":material/error:")

    if training.is_enabled():
        st.space("small")
        with st.expander("이 직무를 준비할 국비 지원 교육과정 보기", icon=":material/school:"):
            training.render(name)

    if not history:
        # 첫 질문 전까지: 입력창 안내 + 은은한 강조 + 입력창으로 포커스
        st.caption("👇 맨 아래 입력창에 질문을 적거나, 위 버튼을 눌러 보세요.")
        st.html(
            "<style>[data-testid='stChatInput']{animation: jdPulse 1.6s ease-in-out 3;}</style>"
        )
        if S.pop("just_chosen", False):
            st.html(
                "<script>setTimeout(()=>{const t=window.parent.document.querySelector("
                "'[data-testid=\"stChatInput\"] textarea')||document.querySelector("
                "'[data-testid=\"stChatInput\"] textarea');if(t){t.focus();t.scrollIntoView({block:'end'});}},400);</script>",
                unsafe_allow_javascript=True,
            )

    prompt = (
        st.chat_input(
            f"{name} 선배에게 궁금한 걸 물어보세요 (예: 신입 연봉은 얼마예요?)",
            key="job_input",
            submit_mode="disable",
        )
        or quick
    )
    if prompt:
        with st.chat_message("user"):
            st.write(prompt)
        if blocked_by_pii(prompt):
            st.stop()
        history.append({"role": "user", "content": prompt})
        with st.chat_message("assistant", avatar="🧑‍💼"):
            if llm.is_enabled():
                with st.spinner("대답을 생각하는 중…"):
                    evidence, sources = job_evidence(name, prompt, S.my_major)
                    clean = [{"role": m["role"], "content": m["content"]} for m in history[-10:]]
                    data, err = llm.generate_json(job_system(name, evidence), clean)
                    reply, used = parse_answer(data)
                    if not reply and data is not None:  # 형식이 어긋난 답이면 한 번만 다시 묻습니다
                        data, err = llm.generate_json(job_system(name, evidence), clean)
                        reply, used = parse_answer(data)
                if not reply:
                    st.warning(err or "답변을 만들지 못했어요. 한 번 더 물어봐 주세요.", icon=":material/error:")
                    history.pop()
                    st.stop()
                st.markdown(reply)
                render_sources(used, sources)
                history.append({"role": "assistant", "content": reply, "sources": used, "found": sources})
                st.stop()
            else:
                reply = f"지금은 시연 모드예요. AI 키가 연결되면 '{name}' 선배가 공공데이터와 현직자 인터뷰를 바탕으로 답해 드려요."
                st.write(reply)
        history.append({"role": "assistant", "content": reply})
    st.stop()

# ════════════════════════════════════════════════════════════
# ① 직무 고르기: 옵션 1(내 학과) · 옵션 2(직접) · 보조(패널에게 이야기)
# ════════════════════════════════════════════════════════════
st.space("small")
opt1, opt2 = st.columns(2, gap="medium")

# ── 옵션 1: 내 학과로 찾기 ───────────────────────────────────
with card("opt-major", "white", parent=opt1):
    option_header(1, "내 학과로 찾기", "학과를 고르면 졸업자가 많이 가는 직업을 보여 줘요.")
    g1, g2 = st.columns(2)
    group = g1.selectbox("계열", majors.fields(), index=None, placeholder="계열 선택", key="opt1_group")
    major = g2.selectbox(
        "학과", majors.majors(group), index=None, placeholder="학과 선택 (검색 가능)", key="opt1_major"
    )
    S.my_major = major
    job1 = None
    if major:
        job1 = st.pills(
            f"{major} 졸업자가 많이 가는 직업",
            majors.top_jobs(major),
            key=f"opt1_job_{major}",
        )
        st.caption(f":material/link: 출처: {majors.SOURCE}")
    st.button(
        "이 직무로 대화하기" if job1 else "직무를 하나 골라 주세요",
        key="opt1_go",
        type="primary",
        width="stretch",
        icon=":material/forum:",
        disabled=not job1,
        on_click=choose,
        args=({"name": job1 or "", "why": f"{major} 졸업자가 많이 진출하는 직업이에요.", "basis": majors.SOURCE},),
    )

# ── 옵션 2: 직접 고르기 ──────────────────────────────────────
with card("opt-direct", "white", parent=opt2):
    option_header(2, "직무 직접 고르기", "궁금한 직무가 있다면 목록에서 고르거나 이름을 입력해요.")
    job2 = st.selectbox(
        "직무 이름",
        recommend_candidates(S.my_major),
        index=None,
        placeholder="예: 데이터 분석가, UX/UI디자이너",
        accept_new_options=True,
        key="opt2_job",
    )
    st.button(
        "이 직무로 대화하기" if job2 else "직무를 골라 주세요",
        key="opt2_go",
        type="primary",
        width="stretch",
        icon=":material/forum:",
        disabled=not job2,
        on_click=choose,
        args=({"name": job2 or "", "why": "", "basis": "직접 선택"},),
    )

# ── 보조: 잘 모르겠다면 패널에게 이야기 ──────────────────────
st.space("medium")
st.subheader("잘 모르겠다면 패널에게 이야기해 보세요", anchor=False)
st.caption("좋아하는 것, 전공, 고민을 말하면 패널이 살펴볼 만한 직무를 3~4개 추천해요.")

for msg in S.panel_explore:
    with st.chat_message(msg["role"], avatar="🎤" if msg["role"] == "assistant" else None):
        st.markdown(msg["content"])

examples = [
    "게임을 좋아하는데 어떤 직업이 있을까요?",
    "사람을 돕는 일을 하고 싶어요",
    "데이터 쪽으로 가고 싶은데 비전공자예요",
]
picked_example = None
if not S.panel_explore:
    picked_example = st.pills("이렇게 시작해 보세요", examples, key="panel_examples", label_visibility="collapsed")

prompt = st.chat_input("패널에게 진로 고민을 이야기해 보세요", key="explore_input", submit_mode="disable")
if picked_example and not prompt:
    prompt = picked_example

if prompt:
    with st.chat_message("user"):
        st.write(prompt)
    if not blocked_by_pii(prompt):
        S.panel_explore.append({"role": "user", "content": prompt})
        candidates = recommend_candidates(S.my_major)
        with st.chat_message("assistant", avatar="🎤"):
            if llm.is_enabled():
                with st.spinner("패널이 어울리는 직무를 고르고 있어요"):
                    data, err = llm.generate_json(
                        recommend_system(candidates, majors.evidence(S.my_major)), S.panel_explore[-8:]
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
                pool = majors.top_jobs(S.my_major) if S.my_major else [p["role"] for p in PANELS["게임 개발"]]
                message = "지금은 시연 모드라 예시로 추천해 드릴게요."
                recs = [{"name": n, "why": "", "basis": majors.SOURCE if S.my_major else "잡담 예시 패널"} for n in pool[:4]]
            st.markdown(message)
        S.panel_explore.append({"role": "assistant", "content": message})
        if recs:
            S.panel_recs = recs
        st.rerun()

# ② 패널 추천 직무 카드
if S.panel_recs:
    st.space("small")
    st.markdown("#### 패널이 추천한 직무")
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
                "이 직무로 대화하기",
                key=f"pick_{i}",
                icon=":material/forum:",
                type="primary",
                width="stretch",
                on_click=choose,
                args=(rec,),
            )

st.caption(f"답변 모드: {'균형(공공데이터 + AI 일반 지식)' if answer_mode() == 'balanced' else '근거 우선'}")
