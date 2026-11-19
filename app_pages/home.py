import streamlit as st

from utils import majors, profile
from utils.evidence import recommend_candidates
from utils.style import big_number, card, hero_emoji

# ── 1. 잡담은 무엇인가 (주제) ─────────────────────────────────
with card("intro-hero", "white"):
    pic, msg = st.columns([1, 4], vertical_alignment="center")
    with pic:
        hero_emoji("💬")
    with msg:
        st.caption("2026 대한민국 청년 CAREER FAIR AI 해커톤")
        st.markdown("## 잡담(Job談) · 일(Job)에 대한 이야기(談)")
        st.markdown(
            "**공공데이터로 말하는 현직자 AI 선배와 '3년 뒤의 나'가 청년의 진로 고민을 함께 풀어 주는 서비스**예요. "
            "검색 결과 목록 대신 대화로, 추측 대신 고용24·KOSIS 같은 공식 숫자로, 한 사람의 말 대신 여러 관점으로 진로를 비교해 봐요."
        )

# ── 2. 왜 만들었나 ────────────────────────────────────────────
st.space("small")
st.subheader("왜 만들었나요?", anchor=False)
st.markdown(
    "청년은 직무의 현실을 모른 채 첫 직장을 고르고, **1년 반 만에** 떠나요. "
    "물어볼 현직자는 없고, 커뮤니티 숫자는 믿기 어렵고, 공식 통계는 너무 어려워요."
)
c1, c2, c3 = st.columns(3, gap="medium")
facts = [
    (c1, "fact-tenure", "1년 6.8개월", "첫 직장 평균 근속기간"),
    (c2, "fact-quit", "44.4%", "첫 직장을 그만둔 이유 1위: 보수·근로시간 불만족"),
    (c3, "fact-first", "11.2개월", "졸업 후 첫 취업까지 걸린 시간"),
]
for col, key, num, label in facts:
    with card(key, "white", parent=col):
        big_number(num)
        st.caption(label)
st.caption(":material/link: 출처: 국가데이터처 경제활동인구조사 청년층 부가조사(2026.5)")

# ── 3. 서비스 안내 (진행 순서) ────────────────────────────────
st.space("small")
st.subheader("이렇게 이용해요", anchor=False)
done = profile.get() is not None
steps = [
    ("1", "직무 간이검사", "가장 먼저 해 주세요! 12문항으로 흥미·가치관·강점을 고르면 이후 대화와 추천이 나에게 맞춰져요.",
     "app_pages/profile.py", "간이검사 시작하기", ":material/person_search:"),
    ("2", "직무 패널", "학과·직업 목록·AI 시대 새 직업에서 직무를 고르고, 그 직무 현직 선배 AI에게 연봉·일과·준비 방법을 물어요.",
     "app_pages/panel.py", "직무 고르러 가기", ":material/groups:"),
    ("3", "3년 뒤의 나", "고른 직무로 취업·대학원·창업 갈림길을 공식 통계로 비교하고, 그 길을 걸은 미래의 나와 대화해요.",
     "app_pages/future.py", "3년 뒤의 나 만나기", ":material/timeline:"),
    ("4", "커리어 로드맵", "지금부터 3년 뒤까지 해야 할 일·자격·국비 교육을 길 위의 이정표로 정리해요.",
     "app_pages/roadmap.py", "로드맵 그리기", ":material/route:"),
]
cols = st.columns(4, gap="small")
for col, (num, title, desc, target, cta, icon) in zip(cols, steps):
    first = num == "1"
    with card(f"step-{num}", "white", parent=col):
        st.html(f'<div class="jd-opt-head"><span class="jd-opt-num">{num}</span>'
                f'<span class="jd-opt-title" style="font-size:1.15rem">{title}</span></div>')
        if first:
            st.badge("완료" if done else "가장 먼저", icon=":material/check:" if done else ":material/flag:",
                     color="green" if done else "blue")
        st.caption(desc)
        primary = (first and not done) or (num == "2" and done)
        if st.button(cta, key=f"home-go-{num}", icon=icon, type="primary" if primary else "secondary", width="stretch"):
            st.switch_page(target)

# ── 4. 한눈에 보는 잡담 ──────────────────────────────────────
st.space("small")
s1, s2, s3 = st.columns(3, gap="medium")
for col, key, label, value, note in [
    (s1, "stat-jobs", "대화할 수 있는 직무", f"{len(recommend_candidates(None))}개", "공공데이터 직업 목록 + AI 시대 새 직업"),
    (s2, "stat-majors", "학과별 진출 직업", f"{len(majors.majors())}개 학과", "한국고용정보원 상위진출직업"),
    (s3, "stat-data", "근거로 쓰는 공공데이터", "4종", "고용24 직업정보·훈련과정, KOSIS, Q-Net"),
]:
    with card(key, "white", parent=col):
        st.markdown(f"**{label}**")
        big_number(value)
        st.caption(note)

st.space("small")
with card("remind", "cream"):
    st.markdown("**지켜요 🔒**")
    st.caption(
        "숫자는 공공데이터만 쓰고 출처를 답변 아래에 보여 줘요. 실명·연락처 같은 개인정보는 받지 않고, "
        "입력한 내용은 저장하지 않아요. 답변은 진로 탐색을 돕는 참고 자료예요."
    )
