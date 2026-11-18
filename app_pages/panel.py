import streamlit as st

from utils import careernet, llm, majors, worknet
from utils.demo_data import DEMO_NOTICE, PANELS
from utils.evidence import panel_evidence, show_sources
from utils.prompts import find_personal_info, panel_system
from utils.style import card, icon_tile

st.title("직무 패널 👥", anchor=False)
st.caption("관심 분야를 고르면 직무별 AI 페르소나가 패널로 등장해 이야기합니다.")

if not llm.is_enabled():
    st.info(DEMO_NOTICE, title="시연 모드", icon=":material/science:")
elif not (careernet.is_enabled() or worknet.is_enabled()):
    st.info(
        "AI 답변은 켜져 있어요. 커리어넷·워크넷 직업정보가 연결되기 전까지는 공공데이터 근거 없이 답하므로, "
        "숫자나 단정적인 사실은 말하지 않아요.",
        title="직업정보 연결 대기 중",
        icon=":material/hourglass_top:",
    )

field = st.pills(
    "관심 분야",
    list(PANELS.keys()),
    default="게임 개발",
    key="panel_field",
)

if not field:
    st.caption("위에서 관심 분야를 하나 골라 주세요.")
    st.stop()

personas = PANELS[field]
roles = [p["role"] for p in personas]

st.space("small")
st.subheader(f"'{field}' 패널", anchor=False)
cols = st.columns(len(personas), gap="medium")
tones = [("sky", "navy"), ("mint", "teal"), ("peach", "peach")]
for i, (col, persona) in enumerate(zip(cols, personas)):
    color, tone = tones[i % len(tones)]
    with card(f"persona-{i}", color, parent=col):
        icon_tile(persona.get("emoji", "🧑‍💼"), f"persona-{i}", tone)
        st.markdown(f"#### {persona['role']}")
        st.badge("AI 페르소나 · 소개 문구", color="gray")
        st.write(persona["says"])

st.space("medium")
st.subheader("패널에게 질문하기", anchor=False)
my_major = majors.render_picker("panel")
st.caption("실명, 연락처 같은 개인정보는 적지 말아 주세요. 적으면 AI에 보내지 않고 다시 물어봐요.")

if "panel_messages" not in st.session_state:
    st.session_state.panel_messages = {}
history: list[dict[str, str]] = st.session_state.panel_messages.setdefault(field, [])

for msg in history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input(f"{field} 패널에게 궁금한 점을 물어보세요", key="panel_input", submit_mode="disable")
if prompt:
    with st.chat_message("user"):
        st.write(prompt)

    pii = find_personal_info(prompt)
    if pii:
        with st.chat_message("assistant"):
            st.warning(
                f"{', '.join(pii)}처럼 보이는 정보가 있어서 AI에 보내지 않았어요. 그 부분을 빼고 다시 물어봐 주세요.",
                icon=":material/lock:",
            )
        st.stop()

    history.append({"role": "user", "content": prompt})
    with st.chat_message("assistant"):
        with st.status("공공 직업정보 찾는 중", type="step") as step:
            evidence, found = panel_evidence(roles, my_major, prompt, field)
            if found:
                st.caption("찾은 근거: " + " · ".join(found))
                step.update(label="공공 직업정보를 찾았어요", state="complete")
            else:
                st.caption("직업정보 연결 전이라 근거자료 없이 답해요.")
                step.update(label="공공데이터 근거 없음 (연결 대기)", state="complete")

        if llm.is_enabled():
            with st.spinner("패널이 답변을 준비하고 있어요"):
                result = llm.generate(panel_system(roles, evidence), history[-10:])
            if result.text:
                reply = result.text
                st.markdown(reply)
                if found:
                    show_sources(found)
                else:
                    st.caption(":material/info: 직업정보 연결 전이라 공공데이터 근거 없이 나눈 일반적인 이야기예요.")
                st.caption(f"AI 답변 · {llm.provider_label()} · 사실과 다를 수 있으니 출처를 함께 확인해 주세요.")
            else:
                st.warning(result.error or "답변을 만들지 못했어요.", icon=":material/error:")
                history.pop()  # 실패한 질문은 대화 기록에 남기지 않습니다
                st.stop()
        else:
            reply = (
                "질문 고마워요! 지금은 시연 모드라 실제 답변을 만들지 않아요. "
                "AI 키가 연결되면 커리어넷 직업정보를 찾아본 뒤, 출처와 함께 답변해 드릴게요."
            )
            st.write(reply)

    history.append({"role": "assistant", "content": reply})
