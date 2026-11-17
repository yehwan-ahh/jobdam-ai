import streamlit as st

from utils.demo_data import DEMO_NOTICE, PANELS
from utils.style import card, icon_tile

st.title("직무 패널 👥", anchor=False)
st.caption("관심 분야를 고르면 직무별 AI 페르소나가 패널로 등장해 이야기합니다.")

st.info(DEMO_NOTICE, title="시연 모드", icon=":material/science:")

field = st.pills(
    "관심 분야",
    list(PANELS.keys()),
    default="게임 개발",
    key="panel_field",
)

if not field:
    st.caption("위에서 관심 분야를 하나 골라 주세요.")
    st.stop()

st.space("small")
st.subheader(f"'{field}' 패널", anchor=False)
cols = st.columns(len(PANELS[field]), gap="medium")
tones = [("sky", "navy"), ("mint", "teal"), ("peach", "peach")]
for i, (col, persona) in enumerate(zip(cols, PANELS[field])):
    color, tone = tones[i % len(tones)]
    with card(f"persona-{i}", color, parent=col):
        icon_tile(persona.get("emoji", "🧑‍💼"), f"persona-{i}", tone)
        st.markdown(f"#### {persona['role']}")
        st.badge("AI 페르소나 · 예시 답변", color="gray")
        st.write(persona["says"])

st.space("medium")
st.subheader("패널에게 질문하기", anchor=False)

if "panel_messages" not in st.session_state:
    st.session_state.panel_messages = {}
history: list[dict[str, str]] = st.session_state.panel_messages.setdefault(field, [])

for msg in history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

prompt = st.chat_input(f"{field} 패널에게 궁금한 점을 물어보세요", key="panel_input")
if prompt:
    history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    reply = (
        "질문 고마워요! 지금은 시연 모드라 실제 답변을 만들지 않아요. "
        "API 연동 후에는 커리어넷 직업정보를 찾아본 뒤, 출처와 함께 답변해 드릴게요."
    )
    with st.chat_message("assistant"):
        with st.status("커리어넷 직업정보 검색 (연동 예정)", type="step", state="complete"):
            st.caption(f"검색어: {field}")
        st.write(reply)
    history.append({"role": "assistant", "content": reply})
