"""직무 간이검사: 간이 흥미 체크 + 가치관·강점 + (선택) 공식 검사 결과 입력 → 직무 적합도."""

import altair as alt
import pandas as pd
import streamlit as st

from utils import majors, profile
from utils.demo_data import PANELS
from utils.prompts import find_personal_info
from utils.style import card

S = st.session_state
st.title("직무 간이검사 🧭", anchor=False)
st.caption(
    "3분이면 끝나요. 고른 성향은 '3년 뒤의 나'와 직무 선배의 대답, 직무 적합도에 쓰여요. "
    "이 창을 닫으면 사라지고, 서버에 저장하지 않아요."
)

saved = profile.get() or {}

with st.form("profile_form", border=False):
    # ── 1. 간이 흥미 체크 ──────────────────────────────────────
    with card("pf-interest", "white"):
        st.markdown("#### 1. 나는 어떤 일에 끌릴까? (간이 흥미 체크 12문항)")
        st.caption("정답은 없어요. 문항마다 지금의 나와 가장 가까운 칸을 하나씩 골라 주세요. 공식 심리검사가 아닌 참고용 체크예요.")
        prev = saved.get("answers") or [None] * len(profile.ITEMS)
        answers = []
        for i, (_, q) in enumerate(profile.ITEMS):
            with st.container(key=f"pfq-row-{i}"):
                st.html(f'<div class="jd-q"><span class="jd-q-num">{i + 1}</span>{q}</div>')
                answers.append(
                    st.segmented_control(
                        f"{i + 1}번 응답", profile.SCALE, default=prev[i], key=f"pf_q{i}",
                        label_visibility="collapsed", width="stretch",
                    )
                )

    st.space("small")
    # ── 2. 가치관·강점 ────────────────────────────────────────
    with card("pf-values", "white"):
        st.markdown("#### 2. 일할 때 중요한 것과 나의 강점")
        values = st.multiselect(
            "일할 때 가장 중요한 가치 (중요한 순서대로 최대 3개)",
            profile.VALUES, default=saved.get("values") or [], max_selections=3, key="pf_values",
        )
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            abilities = st.multiselect(
                "자신 있는 능력 (최대 5개)", profile.ABILITIES, default=saved.get("abilities") or [],
                max_selections=5, key="pf_abil",
            )
        with c2:
            traits = st.multiselect(
                "나를 잘 설명하는 성격 (최대 3개)", profile.TRAITS, default=saved.get("traits") or [],
                max_selections=3, key="pf_traits",
            )
        likes = st.text_area(
            "좋아하는 것이나 해 본 경험 (선택)",
            value=saved.get("likes", ""),
            placeholder="예: 동아리에서 행사 기획을 맡았어요. 데이터로 근거를 찾는 게 재밌었어요.",
            max_chars=200, key="pf_likes",
        )

    # ── 3. 공식 검사 결과 (선택, 끌 수 있음) ───────────────────
    test: dict = {}
    if profile.test_input_enabled():
        st.space("small")
        with card("pf-test", "mint"):
            st.markdown("#### 3. 공식 검사 결과가 있다면 (선택)")
            st.caption(
                "커리어넷·고용24에서 직업심리검사를 했다면 결과를 옮겨 적어 주세요. 입력하면 간이 체크보다 우선해서 써요. "
                "[커리어넷 진로심리검사](https://www.career.go.kr/cnet/front/inspct/inspctMain.do) · "
                "[고용24 직업심리검사](https://www.work24.go.kr)"
            )
            old = saved.get("test") or {}
            t1, t2, t3 = st.columns([1.2, 1, 1.2], gap="medium")
            with t1:
                name = st.selectbox(
                    "검사 이름", profile.TESTS, index=profile.TESTS.index(old["name"]) if old.get("name") in profile.TESTS else None,
                    placeholder="검사를 골라 주세요", key="pf_test_name",
                )
            with t2:
                codes = st.multiselect(
                    "흥미 유형 상위 (최대 2개)", list(profile.RIASEC), default=old.get("riasec") or [],
                    format_func=lambda c: profile.RIASEC[c], max_selections=2, key="pf_test_riasec",
                )
            with t3:
                tvals = st.multiselect(
                    "결과의 상위 가치 (최대 3개)", profile.VALUES, default=old.get("values") or [],
                    max_selections=3, key="pf_test_values",
                )
            if name and (codes or tvals):
                test = {"name": name, "riasec": codes, "values": tvals}

    st.space("small")
    submitted = st.form_submit_button("프로필 저장하고 결과 보기", type="primary", icon=":material/check:", width="stretch")

if submitted:
    missing = [str(i + 1) for i, a in enumerate(answers) if not a]
    if missing:
        st.warning(f"아직 고르지 않은 문항이 있어요: {', '.join(missing)}번. 모든 문항에 답해 주세요.", icon=":material/edit_note:")
        st.stop()
    pii = find_personal_info(likes)
    if pii:
        st.warning(f"{', '.join(pii)}처럼 보이는 정보가 있어서 저장하지 않았어요. 그 부분을 빼고 다시 저장해 주세요.", icon=":material/lock:")
        st.stop()
    profile.save({
        "answers": answers, "riasec": profile.riasec_scores(answers), "values": values,
        "abilities": abilities, "traits": traits, "likes": likes.strip(), "test": test,
    })
    st.toast("프로필을 저장했어요", icon=":material/check:")

p = profile.get()
if not p:
    st.stop()

# ── 결과 ─────────────────────────────────────────────────────
st.space("medium")
st.subheader("나의 성향 요약", anchor=False)
ri = profile.effective_riasec(p)
top = profile.top_codes(ri, 2)
left, right = st.columns([1.1, 1], gap="medium")
with card("pf-result", "white", parent=left):
    st.markdown(f"### {' · '.join(profile.RIASEC[c] for c in top)}")
    st.markdown(" / ".join(profile.RIASEC_DESC[c] for c in top) + "에 끌리는 편이에요.")
    df = pd.DataFrame({"유형": [profile.RIASEC[c] for c in profile.RIASEC], "점수": [ri[c] for c in profile.RIASEC]})
    df["강조"] = df["유형"].isin([profile.RIASEC[c] for c in top]).map({True: "상위", False: "기타"})
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            y=alt.Y("유형:N", sort=list(df["유형"]), title=None),
            x=alt.X("점수:Q", scale=alt.Scale(domain=[0, 100]), title=None),
            color=alt.Color("강조:N", scale=alt.Scale(domain=["상위", "기타"], range=["#111111", "#C8C8C8"]), legend=None),
            tooltip=["유형", "점수"],
        )
        .properties(height=210)
        .configure_view(strokeWidth=0)
        .configure_axis(grid=False, labelColor="#555555", domainColor="#D4D4D4")
    )
    st.altair_chart(chart, width="stretch")
    src = (p.get("test") or {}).get("name") if profile.test_input_enabled() else None
    st.caption(f":material/info: {'입력한 공식 검사(' + src + ') 결과 기준' if src and (p.get('test') or {}).get('riasec') else '간이 흥미 체크 기준 · 공식 검사가 아니에요'}")
with card("pf-values-res", "white", parent=right):
    st.markdown("**중요한 가치** · " + (", ".join(profile.effective_values(p)) or "고르지 않음"))
    st.markdown("**강점** · " + (", ".join(p.get("abilities") or []) or "고르지 않음"))
    st.markdown("**성격** · " + (", ".join(p.get("traits") or []) or "고르지 않음"))
    if p.get("likes"):
        st.markdown(f"**좋아하는 것·경험** · {p['likes']}")
    st.space("small")
    with st.container(horizontal=True):
        if st.button("직무 패널로 가기", icon=":material/groups:", type="primary"):
            st.switch_page("app_pages/panel.py")
        if st.button("3년 뒤의 나 만나기", icon=":material/timeline:"):
            st.switch_page("app_pages/future.py")
        if st.button("프로필 지우기", icon=":material/delete:"):
            profile.clear()
            st.rerun()

# ── 직무 적합도 (공공데이터) ─────────────────────────────────
st.space("medium")
st.subheader("나와 잘 맞는 직무 찾기", anchor=False)
st.caption("고용24 직업정보에 직업마다 들어 있는 흥미·가치관·능력 점수와 내 검사 결과를 비교한 참고 지표예요.")
pool: list[str] = []
if S.get("my_major"):
    pool += majors.top_jobs(S["my_major"])
for personas in PANELS.values():
    pool += [x["role"] for x in personas]
pool = list(dict.fromkeys(pool))
choices = st.multiselect(
    "비교할 직무 (최대 8개)", pool, default=pool[:6], max_selections=8, accept_new_options=True, key="pf_fit_jobs",
    help="목록에 없는 직무도 이름을 입력해 추가할 수 있어요.",
)
if st.button("적합도 계산하기", icon=":material/calculate:"):
    rows = []
    with st.spinner("고용24 직업정보에서 성향 점수를 불러오는 중…"):
        for job in choices:
            t = profile.job_traits(job)
            if t:
                f = profile.fit(p, t)
                rows.append({"직무": job, "고용24 직업명": t["name"], "적합도": f["total"], "흥미": f["interest"],
                             "가치관": f["values"], "강점": f["strength"], "채우면 좋은 능력": ", ".join(f["gaps"])})
    if rows:
        S.pf_fit_rows = sorted(rows, key=lambda r: -r["적합도"])
    else:
        st.info("고용24에서 성향 점수를 찾지 못했어요. 직무 이름을 바꿔 보세요.")
if S.get("pf_fit_rows"):
    st.dataframe(
        pd.DataFrame(S.pf_fit_rows),
        hide_index=True,
        column_config={"적합도": st.column_config.ProgressColumn("적합도", min_value=0, max_value=100, format="%d점")},
    )
    st.caption(":material/link: 출처: 고용24 직업정보(한국고용정보원, 공공누리 제4유형)의 직업 흥미·가치관·능력 점수 · 참고 지표예요.")
