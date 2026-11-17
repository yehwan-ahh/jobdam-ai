import streamlit as st

st.badge("2026 청년 CAREER FAIR AI 해커톤 출품작", icon=":material/emoji_events:", color="blue")
st.title("잡담, 진로 고민을 함께 나누는 AI", anchor=False)
st.markdown(
    "#### 현직자 AI 패널과 '3년 뒤의 나'가 공공데이터를 근거로 함께 고민해 드려요."
)

with st.container(horizontal=True):
    st.badge("공공데이터 근거", icon=":material/verified:", color="green")
    st.badge("모든 답변에 출처 표시", icon=":material/link:", color="green")
    st.badge("개인정보 미수집", icon=":material/lock:", color="green")

st.space("small")
with st.container(horizontal=True):
    st.page_link("app_pages/panel.py", label="직무 패널 열기", icon=":material/groups:")
    st.page_link("app_pages/future.py", label="3년 뒤의 나 만나기", icon=":material/timeline:")

st.space("large")

st.subheader("이런 고민, 혼자 하고 있나요?", anchor=False)
st.space("small")
c1, c2, c3 = st.columns(3, gap="medium")
with c1.container(border=True, height="stretch"):
    st.markdown("**:blue[:material/help:] 무슨 일을 하는지 모르겠어요**")
    st.caption("직무 이름은 아는데 실제로 하루를 어떻게 보내는지는 알기 어렵습니다.")
with c2.container(border=True, height="stretch"):
    st.markdown("**:blue[:material/person_off:] 물어볼 현직자가 없어요**")
    st.caption("주변에 해당 분야 선배가 없으면 정보가 커뮤니티 후기에만 의존하게 됩니다.")
with c3.container(border=True, height="stretch"):
    st.markdown("**:blue[:material/alt_route:] 갈림길에서 결정을 못 하겠어요**")
    st.caption("취업, 대학원, 창업 중 무엇이 나은지 근거를 갖고 비교하기 어렵습니다.")

st.space("large")

st.subheader("잡담이 도와주는 두 가지 방법", anchor=False)
st.space("small")
left, right = st.columns(2, gap="medium")
with left.container(border=True, height="stretch"):
    st.markdown("### :green[:material/groups:] 직무 패널")
    st.markdown(
        "관심 분야를 입력하면 직무별 AI 페르소나가 **패널 토크**처럼 등장해 "
        "업무, 필요 역량, 전망을 이야기합니다. 궁금한 점은 이어서 질문할 수 있어요."
    )
    st.page_link("app_pages/panel.py", label="패널 열기", icon=":material/arrow_forward:")
with right.container(border=True, height="stretch"):
    st.markdown("### :green[:material/timeline:] 3년 뒤의 나")
    st.markdown(
        "취업, 대학원, 창업 중 갈림길을 고르면 각 길을 걸은 '**3년 뒤의 나**'가 "
        "공식 통계를 바탕으로 좋았던 점과 아쉬웠던 점을 들려줍니다."
    )
    st.page_link("app_pages/future.py", label="미래의 나 만나기", icon=":material/arrow_forward:")

st.space("large")

st.subheader("이렇게 작동해요", anchor=False)
st.space("small")
s1, s2, s3, s4 = st.columns(4, gap="medium")
steps = [
    (":material/edit:", "1. 고민 입력", "관심 분야나 갈림길을 고릅니다. 실명·연락처 같은 개인정보는 받지 않아요."),
    (":material/database:", "2. 근거 찾기", "커리어넷 직업정보와 KOSIS 통계에서 관련 데이터를 찾습니다."),
    (":material/smart_toy:", "3. AI 페르소나 대화", "찾은 근거를 바탕으로 페르소나가 대화체로 설명합니다."),
    (":material/fact_check:", "4. 출처 표시", "모든 답변에 근거 출처를 달고, 추정인 내용은 추정이라고 밝힙니다."),
]
for col, (icon, title, desc) in zip((s1, s2, s3, s4), steps):
    with col.container(border=True, height="stretch"):
        st.markdown(f"**:green[{icon}] {title}**")
        st.caption(desc)
