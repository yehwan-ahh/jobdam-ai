import streamlit as st

from utils.demo_data import DEMO_NOTICE, FUTURES

st.title("3년 뒤의 나", anchor=False)
st.caption("갈림길을 고르면 그 길을 걸은 '3년 뒤의 나'가 좋았던 점과 아쉬웠던 점을 들려줍니다.")

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

with st.chat_message("assistant", avatar=str(future["icon"])):
    st.markdown(f"**{future['headline']}**")
    st.write(future["says"])

good, bad = st.columns(2)
with good.container(border=True, height="stretch"):
    st.markdown("**:green[:material/thumb_up:] 좋았던 점**")
    for item in future["pros"]:  # type: ignore[union-attr]
        st.markdown(f"- {item}")
with bad.container(border=True, height="stretch"):
    st.markdown("**:orange[:material/warning:] 아쉬웠던 점**")
    for item in future["cons"]:  # type: ignore[union-attr]
        st.markdown(f"- {item}")

with st.container(border=True):
    st.markdown("**:material/bar_chart: 함께 확인할 공식 통계 (KOSIS 연동 예정)**")
    for item in future["check"]:  # type: ignore[union-attr]
        st.markdown(f"- {item}")
    st.caption("연동 후에는 실제 통계 수치와 출처 링크가 이곳에 표시됩니다.")

st.space("small")
st.markdown("##### 세 갈림길 한눈에 비교")
st.table(
    {
        "갈림길": list(FUTURES.keys()),
        "3년 뒤의 나": [str(f["headline"]) for f in FUTURES.values()],
        "가장 큰 장점": [f["pros"][0] for f in FUTURES.values()],  # type: ignore[index]
        "가장 큰 부담": [f["cons"][0] for f in FUTURES.values()],  # type: ignore[index]
    }
)
