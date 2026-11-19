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
            "데이터": [
                "커리어넷 직업정보(직업백과) Open API",
                "고용24 직업정보 Open API (구 워크넷)",
                "고용24 국민내일배움카드 훈련과정 Open API",
                "상위진출직업 (2022-04-06)",
                "국가통계포털(KOSIS) OpenAPI",
            ],
            "제공기관": ["한국직업능력연구원", "한국고용정보원", "고용노동부·한국고용정보원", "한국고용정보원", "국가데이터처"],
            "활용": [
                "직무별 업무·필요 역량·전망",
                "하는 일·임금·만족도·전망·관련 자격 (원문 인용)",
                "선택한 직무를 준비할 국비 지원 교육과정 추천",
                "학과별 졸업자가 많이 진출하는 직업",
                "취업률·임금·창업 생존율 등 통계",
            ],
            "이용조건": [
                "공공누리 제1유형(출처표시)",
                "공공누리 제4유형(출처표시·비영리·변경금지)",
                "고용24 OPEN-API 이용약관 (출처표시)",
                "공공데이터포털 파일데이터 (출처표시)",
                "KOSIS 통계정보활용약관",
            ],
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
    (c2, "mint", "teal", "🧭", "숫자는 공공데이터만", "연봉·비율 같은 숫자는 공공데이터에 있을 때만 말하고, 경험담·조언은 AI 일반 지식임을 답변 아래에 밝힙니다."),
    (c3, "peach", "peach", "🔒", "개인정보 미수집", "실명·연락처 등 개인정보를 받거나 저장하지 않으며, 시연에는 가상 데이터만 씁니다."),
]
for col, color, tone, emoji, title, desc in principles:
    with card(f"rule-{tone}", color, parent=col):
        icon_tile(emoji, f"rule-{tone}", tone)
        st.markdown(f"#### {title}")
        st.caption(desc)

st.space("small")
with card("limits", "white"):
    st.markdown("#### AI의 한계와 대응")
    st.table(
        {
            "한계": [
                "AI가 사실과 다른 내용을 말할 수 있어요",
                "숫자를 지어내거나 잘못 옮길 수 있어요",
                "공공데이터에 없는 직무·최신 정보가 있어요",
                "사용자가 개인정보를 적을 수 있어요",
                "진로를 단정하거나 한쪽으로 몰 수 있어요",
            ],
            "잡담의 대응": [
                "검색한 공공데이터를 근거로 답하고, 출처를 답변 아래에 항목별로 보여 줘요",
                "숫자는 근거에 있을 때만 쓰고, 금액은 코드에서 미리 읽기 쉬운 형식으로 바꿔 넘겨요",
                "가장 가까운 직업 정보를 '관련 직업'으로 밝히고, 나머지는 AI 일반 지식이라고 표시해요",
                "전화번호·이메일·주민번호가 보이면 AI에 보내지 않고 다시 묻게 해요",
                "결과를 보장하지 않고, 좋은 점과 힘든 점을 함께 말하며 마지막에 스스로 생각할 질문을 던져요",
            ],
        }
    )

st.space("small")
with card("notice", "cream"):
    st.markdown("**이용 안내**")
    st.caption("잡담의 답변은 진로 탐색을 돕는 참고 자료이며, 전문 상담을 대신하지 않습니다.")
