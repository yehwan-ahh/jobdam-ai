import streamlit as st

from utils.kosis import TABLES
from utils.style import card, icon_tile

st.title("데이터와 원칙 📎", anchor=False)
st.caption("잡담이 어떤 데이터를 근거로 답하고, 어떤 원칙을 지키는지 정리했습니다.")

st.space("small")
with card("sources", "white"):
    st.markdown("#### 데이터 출처")
    st.table(
        {
            "데이터": ["커리어넷 직업정보(직업백과) Open API", "국가통계포털(KOSIS) OpenAPI"],
            "제공기관": ["한국직업능력연구원", "국가데이터처"],
            "활용": ["직무별 업무·필요 역량·전망", "취업률·임금·창업 생존율 등 통계"],
            "이용조건": ["공공누리 제1유형(출처표시)", "KOSIS 통계정보활용약관"],
        }
    )

st.space("small")
with card("kosis-tables", "white"):
    st.markdown("#### 사용할 KOSIS 통계표")
    st.table(
        {
            "통계표": [f"[{t.title}]({t.url})" for t in TABLES.values()],
            "작성기관·통계": [t.source for t in TABLES.values()],
            "수록기간": [t.years for t in TABLES.values()],
            "통계표 ID": [f"{t.org_id} / {t.tbl_id}" for t in TABLES.values()],
        }
    )

st.space("small")
st.subheader("답변 원칙", anchor=False)
c1, c2, c3 = st.columns(3, gap="medium")
principles = [
    (c1, "sky", "navy", "🔗", "출처 표시", "모든 답변에 근거가 된 데이터 출처를 함께 보여 줍니다."),
    (c2, "mint", "teal", "🧭", "추정은 추정이라고", "데이터로 확인할 수 없는 내용은 AI의 추정임을 분명히 밝힙니다."),
    (c3, "peach", "peach", "🔒", "개인정보 미수집", "실명·연락처 등 개인정보를 받거나 저장하지 않으며, 시연에는 가상 데이터만 씁니다."),
]
for col, color, tone, emoji, title, desc in principles:
    with card(f"rule-{tone}", color, parent=col):
        icon_tile(emoji, f"rule-{tone}", tone)
        st.markdown(f"#### {title}")
        st.caption(desc)

st.space("small")
with card("notice", "cream"):
    st.markdown("**💛 이용 안내**")
    st.caption("잡담의 답변은 진로 탐색을 돕는 참고 자료이며, 전문 상담을 대신하지 않습니다.")
