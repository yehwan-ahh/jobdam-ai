import streamlit as st

st.title("데이터와 원칙", anchor=False)
st.caption("잡담이 어떤 데이터를 근거로 답하고, 어떤 원칙을 지키는지 정리했습니다.")

st.subheader("데이터 출처")
st.table(
    {
        "데이터": ["커리어넷 직업정보(직업백과) Open API", "국가통계포털(KOSIS) OpenAPI"],
        "제공기관": ["한국직업능력연구원", "국가데이터처"],
        "활용": ["직무별 업무·필요 역량·전망", "취업률·임금·창업 생존율 등 통계"],
        "이용조건": ["공공누리 제1유형(출처표시)", "KOSIS 통계정보활용약관"],
    }
)

st.subheader("답변 원칙")
c1, c2, c3 = st.columns(3, gap="medium")
with c1.container(border=True, height="stretch"):
    st.markdown("**:green[:material/link:] 출처 표시**")
    st.caption("모든 답변에 근거가 된 데이터 출처를 함께 보여 줍니다.")
with c2.container(border=True, height="stretch"):
    st.markdown("**:green[:material/report:] 추정은 추정이라고**")
    st.caption("데이터로 확인할 수 없는 내용은 AI의 추정임을 분명히 밝힙니다.")
with c3.container(border=True, height="stretch"):
    st.markdown("**:green[:material/lock:] 개인정보 미수집**")
    st.caption("실명·연락처 등 개인정보를 받거나 저장하지 않으며, 시연에는 가상 데이터만 씁니다.")

st.warning(
    "잡담의 답변은 진로 탐색을 돕는 참고 자료이며, 전문 상담을 대신하지 않습니다.",
    title="이용 안내",
    icon=":material/info:",
)
