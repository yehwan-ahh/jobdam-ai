import streamlit as st

from utils import compare, kosis, llm, profile
from utils.demo_data import DEMO_NOTICE, FUTURES
from utils.evidence import future_evidence, show_sources
from utils.prompts import find_personal_info, future_system
from utils.style import card, hero_emoji, icon_tile, scroll_to_top

st.title("3년 뒤의 나 🔭", anchor=False)
if not any(st.session_state.get("future_messages", {}).values()) and not st.session_state.get("future_jump"):
    scroll_to_top()
st.caption("갈림길을 고르면 그 길을 걸은 '3년 뒤의 나'가 좋았던 점과 아쉬웠던 점을 들려줍니다.")
target_job = (st.session_state.get("selected_job") or {}).get("name")
_me = profile.get()
with st.container(horizontal=True):
    if target_job:
        st.badge(f"직무 패널에서 고른 직무: {target_job}", icon=":material/work:", color="blue")
    if _me:
        st.badge(f"직무 간이검사: {profile.summary_line(_me)}", icon=":material/person_search:", color="gray")
if not _me:
    st.caption(":material/person_search: '직무 간이검사'를 하면 3년 뒤의 내가 내 성향·가치관에 맞춰 이야기해요.")

if not llm.is_enabled():
    st.info(DEMO_NOTICE, title="시연 모드", icon=":material/science:")

# 순서: 직무 간이검사 → 직무 패널에서 직업 고르기 → 3년 뒤의 나
if not target_job:
    st.space("small")
    with card("future-gate", "white"):
        st.markdown("#### 먼저 직무 패널에서 직업을 골라 주세요")
        st.markdown(
            "'3년 뒤의 나'는 고른 직업을 목표로 걸어간 미래의 내가 이야기해요. "
            "**① 직무 간이검사 → ② 직무 패널에서 직업 고르기 → ③ 3년 뒤의 나** 순서로 진행해요."
        )
        with st.container(horizontal=True):
            if st.button("직무 패널에서 직업 고르기", type="primary", icon=":material/groups:"):
                st.switch_page("app_pages/panel.py")
            if not _me and st.button("직무 간이검사부터 하기", icon=":material/person_search:"):
                st.switch_page("app_pages/profile.py")
    st.stop()

EMOJI = {"취업/이직": "🧑‍💼", "대학원 진학": "🧑‍🔬", "창업": "🧑‍🚀"}


def pick_path(path: str) -> None:
    st.session_state.future_choice = path
    st.session_state.future_jump = True


# ── 종합: 직무 간이검사 + 직무 패널 → 나에게 맞는 갈림길 ─────────
rec = profile.recommend_path(_me) if _me else []
st.space("small")
with st.container(key="future-synth"):
    st.html('<div class="jd-report-tag">🧩 직무 간이검사 + 직무 패널 종합</div>')
    a1, a2, a3 = st.columns([1, 1.15, 1.35], gap="medium")
    with card("syn-me", "white", parent=a1):
        st.caption("① 직무 간이검사")
        if _me:
            st.markdown(f"**{profile.summary_line(_me)}**")
            st.caption("강점: " + (", ".join((_me.get("abilities") or [])[:3]) or "고르지 않음"))
        else:
            st.markdown("아직 검사 전이에요")
            if st.button("간이검사 하기", icon=":material/person_search:", key="syn-do-test"):
                st.switch_page("app_pages/profile.py")
    with card("syn-job", "white", parent=a2):
        st.caption("② 직무 패널에서 고른 직무")
        st.markdown(f"**{target_job}**")
        profile.render_fit(target_job, "future")
    with card("syn-path", "white", parent=a3):
        st.caption("③ 나에게 맞는 갈림길 (참고 추천)")
        if rec:
            best = rec[0]
            st.markdown(f"### {EMOJI.get(best['path'], '')} {best['path']} 추천")
            st.markdown(f"{best['reason']}. {best['about']}이에요.")
            for r in rec:
                st.progress(r["score"] / 100, text=f"{r['path']} {r['score']}점")
            st.caption(":material/info: 간이검사의 흥미 유형·가치관으로 계산한 참고 지표예요. 정답이 아니니 세 길을 모두 비교해 보세요.")
        else:
            st.markdown("간이검사를 하면 취업·대학원·창업 중 나에게 맞는 길을 추천해 줘요.")

# ── 갈림길 한눈에 비교 (KOSIS 실제 값) ─────────────────────────
if kosis.is_enabled():
    st.space("small")
    st.subheader("갈림길 한눈에 비교", anchor=False)
    st.caption(
        (f"'{target_job}'을(를) 목표로 할 때 " if target_job else "")
        + "세 갈림길을 공식 통계로 나란히 봐요. 숫자는 모두 KOSIS 원자료 값이에요."
    )
    cols = st.columns(3, gap="medium")
    for col, path in zip(cols, FUTURES.keys()):
        with card(f"cmp-{path}", "white", parent=col):
            st.markdown(f"#### {EMOJI.get(path, '')} {path}")
            if rec and rec[0]["path"] == path:
                st.badge("간이검사 추천", icon=":material/star:", color="blue")
            with st.spinner("통계를 불러오는 중…"):
                s = compare.stats(path)
            if s.error:
                st.caption(f"이 길의 통계를 아직 불러오지 못했어요. ({s.error})")
            else:
                for label, value in s.metrics:
                    st.metric(label, value)
                if s.chart is not None:
                    st.caption(s.caption)
                    st.altair_chart(s.chart, width="stretch")
                st.caption(f":material/link: {s.source}, KOSIS")
            st.button(
                "이 길의 나와 대화하기",
                key=f"talk-{path}",
                icon=":material/forum:",
                type="primary" if st.session_state.get("future_choice") == path else "secondary",
                on_click=pick_path,
                args=(path,),
                width="stretch",
            )

st.space("small")
choice = st.segmented_control(
    "어떤 갈림길이 궁금한가요?",
    list(FUTURES.keys()),
    default=rec[0]["path"] if rec else "취업/이직",
    key="future_choice",
)

if not choice:
    st.caption("위에서 갈림길을 하나 골라 주세요.")
    st.stop()

future = FUTURES[choice]

st.space("small")
with card("future-hero", "sky"):
    pic, msg = st.columns([1, 4], vertical_alignment="center")
    with pic:
        hero_emoji(EMOJI.get(choice, "🙂"))
    with msg:
        st.badge("3년 뒤의 나 · 예시 대화", color="blue")
        st.markdown(f"### {future['headline']}")
        st.markdown(f"“{future['says']}”")

st.space("small")
good, bad, stat = st.columns(3, gap="medium")
with card("pros", "mint", parent=good):
    icon_tile("👍", "pros", "teal")
    st.markdown("#### 좋았던 점")
    for item in future["pros"]:  # type: ignore[union-attr]
        st.markdown(f"- {item}")
with card("cons", "peach", parent=bad):
    icon_tile("🤔", "cons", "peach")
    st.markdown("#### 아쉬웠던 점")
    for item in future["cons"]:  # type: ignore[union-attr]
        st.markdown(f"- {item}")
with card("stats", "white", parent=stat):
    icon_tile("📊", "stats", "navy")
    st.markdown("#### 함께 볼 공식 통계")
    for key in kosis.FUTURE_TABLES.get(choice, []):
        t = kosis.TABLES[key]
        st.markdown(f"- [{t.title}]({t.url})  \n  :gray[{t.source}]")
    if kosis.is_enabled():
        st.badge("KOSIS 연결됨", icon=":material/check:", color="green")
    else:
        st.badge("KOSIS 키 대기 중", color="gray")

# ── 3년 뒤의 나와 대화 (아래 채팅창) ─────────────────────────
my_major = st.session_state.get("my_major")
st.space("small")
st.caption(f":material/forum: 맨 아래 채팅창에서 '{choice}'을 고른 3년 뒤의 나와 바로 대화해요. 실명·연락처 같은 개인정보는 적지 말아 주세요.")

if "future_messages" not in st.session_state:
    st.session_state.future_messages = {}
history: list[dict[str, str]] = st.session_state.future_messages.setdefault(choice, [])

for m in history:
    with st.chat_message(m["role"], avatar=EMOJI.get(choice) if m["role"] == "assistant" else None):
        st.markdown(m["content"])

if st.session_state.pop("future_jump", False) and not history:
    st.html(
        "<script>setTimeout(()=>{const t=window.parent.document.querySelector("
        "'[data-testid=\"stChatInput\"] textarea')||document.querySelector("
        "'[data-testid=\"stChatInput\"] textarea');if(t){t.focus();t.scrollIntoView({block:'end'});}},400);</script>",
        unsafe_allow_javascript=True,
    )

prompt = st.chat_input(f"'{choice}'을 고른 3년 뒤의 나에게 물어보세요", key="future_input", submit_mode="disable")
if prompt:
    with st.chat_message("user"):
        st.write(prompt)
    pii = find_personal_info(prompt)
    if pii:
        with st.chat_message("assistant", avatar=EMOJI.get(choice)):
            st.warning(
                f"{', '.join(pii)}처럼 보이는 정보가 있어서 AI에 보내지 않았어요. 그 부분을 빼고 다시 물어봐 주세요.",
                icon=":material/lock:",
            )
        st.stop()

    history.append({"role": "user", "content": prompt})
    with st.chat_message("assistant", avatar=EMOJI.get(choice)):
        if llm.is_enabled():
            with st.spinner("3년 뒤의 내가 생각을 정리하고 있어요"):
                evidence, used = future_evidence(choice, my_major)
                result = llm.generate(future_system(choice, evidence, target_job, profile.prompt_block(target_job)), history[-10:])
            if not result.text:
                st.warning(result.error or "답변을 만들지 못했어요.", icon=":material/error:")
                history.pop()
                st.stop()
            reply = result.text
            st.markdown(reply)
            if used:
                show_sources(used)
            else:
                st.caption(":material/info: KOSIS 연결 전이라 공식 통계 없이 나눈 일반적인 이야기예요.")
            st.caption(f"AI 답변 · {llm.provider_label()} · 개인의 상황에 따라 결과는 달라질 수 있어요.")
        else:
            reply = "지금은 시연 모드라 실제 답변을 만들지 않아요. AI 키가 연결되면 공식 통계를 바탕으로 이야기해 줄게요."
            st.write(reply)
    history.append({"role": "assistant", "content": reply})
