import streamlit as st

from utils import kosis, llm
from utils.demo_data import DEMO_NOTICE, FUTURES
from utils.evidence import future_evidence, show_sources
from utils.prompts import find_personal_info, future_system
from utils.style import card, hero_emoji, icon_tile

st.title("3년 뒤의 나 🔭", anchor=False)
st.caption("갈림길을 고르면 그 길을 걸은 '3년 뒤의 나'가 좋았던 점과 아쉬웠던 점을 들려줍니다.")

if not llm.is_enabled():
    st.info(DEMO_NOTICE, title="시연 모드", icon=":material/science:")

choice = st.segmented_control(
    "어떤 갈림길이 궁금한가요?",
    list(FUTURES.keys()),
    default="취업/이직",
    key="future_choice",
)

if not choice:
    st.caption("위에서 갈림길을 하나 골라 주세요.")
    st.stop()

future = FUTURES[choice]
EMOJI = {"취업/이직": "🧑‍💼", "대학원 진학": "🧑‍🔬", "창업": "🧑‍🚀"}

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

# ── 실제 통계 (KOSIS 연결 시) ─────────────────────────────
if kosis.is_enabled():
    st.space("small")
    with card("kosis-data", "white"):
        st.markdown("#### KOSIS 통계 미리보기")
        for key in kosis.FUTURE_TABLES.get(choice, []):
            t = kosis.TABLES[key]
            df = kosis.fetch(key)
            st.markdown(f"**{t.title}** · [원문 보기]({t.url})")
            if df is None or df.empty:
                st.caption("이 통계표는 아직 불러오지 못했어요. (항목 코드 확인 필요)")
            else:
                st.dataframe(df.head(50), hide_index=True, alt=f"{t.title} 통계 표")
            st.caption(f"출처: {t.source}, KOSIS")

# ── 3년 뒤의 나에게 묻기 ───────────────────────────────────
st.space("medium")
st.subheader("3년 뒤의 나에게 물어보기", anchor=False)
st.caption("실명, 연락처 같은 개인정보는 적지 말아 주세요.")

if "future_messages" not in st.session_state:
    st.session_state.future_messages = {}
history: list[dict[str, str]] = st.session_state.future_messages.setdefault(choice, [])

for m in history:
    with st.chat_message(m["role"], avatar=EMOJI.get(choice) if m["role"] == "assistant" else None):
        st.write(m["content"])

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
                evidence, used = future_evidence(choice)
                result = llm.generate(future_system(choice, evidence), history[-10:])
            if not result.text:
                st.warning(result.error or "답변을 만들지 못했어요.", icon=":material/error:")
                history.pop()
                st.stop()
            reply = result.text
            st.write(reply)
            show_sources(used, "KOSIS")
            st.caption(f"AI 답변 · {llm.provider_label()} · 개인의 상황에 따라 결과는 달라질 수 있어요.")
        else:
            reply = "지금은 시연 모드라 실제 답변을 만들지 않아요. AI 키가 연결되면 공식 통계를 바탕으로 이야기해 줄게요."
            st.write(reply)
    history.append({"role": "assistant", "content": reply})
