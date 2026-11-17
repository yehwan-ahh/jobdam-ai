import streamlit as st

from utils.demo_data import DEMO_NOTICE, FUTURES
from utils.style import card, hero_emoji, icon_tile

st.title("3년 뒤의 나 🔭", anchor=False)
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
    for item in future["check"]:  # type: ignore[union-attr]
        st.markdown(f"- {item}")
    st.badge("KOSIS 연동 예정", color="gray")

st.space("medium")
with card("compare", "white"):
    st.markdown("#### 세 갈림길 한눈에 비교")
    st.table(
        {
            "갈림길": list(FUTURES.keys()),
            "3년 뒤의 나": [str(f["headline"]) for f in FUTURES.values()],
            "가장 큰 장점": [f["pros"][0] for f in FUTURES.values()],  # type: ignore[index]
            "가장 큰 부담": [f["cons"][0] for f in FUTURES.values()],  # type: ignore[index]
        }
    )
