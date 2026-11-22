"""현재의 나 · 직무 간이검사: ① 흥미 12문항 → ② 가치와 강점 → ③ 결과 (UX/UI 디자인 시안의 3단계)."""

import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from utils import majors, profile
from utils.demo_data import PANELS
from utils.prompts import find_personal_info
from utils.style import card

S = st.session_state
saved = profile.get() or {}
if "pf_stage" not in S:
    S.pf_stage = 3 if saved else 1
# 단계를 오가도 고른 답이 남도록, 위젯 값과 별도로 보관해요(안 보이는 위젯의 값은 Streamlit이 지워요).
if "pf_ans" not in S:
    S.pf_ans = list(saved.get("answers") or [None] * len(profile.ITEMS))
if "pf_draft" not in S:
    S.pf_draft = {k: saved.get(k) for k in ("values", "abilities", "traits", "likes", "test")}


def go(stage: int) -> None:
    S.pf_stage = stage
    S.pf_jump = S.get("pf_jump", 0) + 1


def to_top() -> None:
    """단계가 바뀌면 화면 맨 위로."""
    components.html(
        f"<!-- {S.get('pf_jump', 0)} --><script>setTimeout(()=>{{const m=window.parent.document.querySelector('[data-testid=\"stMain\"]');"
        "if(m)m.scrollTo({top:0});window.parent.scrollTo(0,0);},60)</script>",
        height=0,
    )


stage = S.pf_stage
names = ["흥미 12문항", "가치와 강점", "결과"]
tabs = "".join(
    f'<span class="{"on" if i + 1 == stage else ("done" if i + 1 < stage else "")}">{n}</span>' for i, n in enumerate(names)
)
st.html(f'<div class="jd-stage">{tabs}</div>')
if S.get("pf_jump"):
    to_top()

# ── ① 흥미 12문항 ────────────────────────────────────────────
if stage == 1:
    st.title("직무 간이검사", anchor=False)
    st.caption("평소 나와 가까운 답을 골라요. 약 3분이 걸려요. 공식 심리검사가 아닌 참고용 체크이고, 서버에 저장하지 않아요.")
    n_done = sum(1 for i in range(len(profile.ITEMS)) if S.get(f"pf_q{i}", S.pf_ans[i]))
    st.html(
        f'<div class="jd-progress"><span>응답한 문항</span><b>{n_done} / {len(profile.ITEMS)}</b></div>'
        f'<div class="jd-bar"><i style="width:{n_done / len(profile.ITEMS) * 100:.0f}%"></i></div>'
    )
    for i, (_, q) in enumerate(profile.ITEMS):
        with st.container(key=f"pfq-row-{i}"):
            st.html(f'<div class="jd-q"><span class="jd-q-num">{i + 1}.</span>{q}</div>')
            S.pf_ans[i] = st.segmented_control(
                f"{i + 1}번 응답", profile.SCALE, default=S.pf_ans[i], key=f"pf_q{i}",
                label_visibility="collapsed", width="stretch",
            )
    st.space("small")
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("다음", icon=":material/arrow_forward:", icon_position="right", type="primary", key="pf-next1"):
            missing = [str(i + 1) for i, a in enumerate(S.pf_ans) if not a]
            if missing:
                st.warning(f"아직 고르지 않은 문항이 있어요: {', '.join(missing)}번", icon=":material/edit_note:")
            else:
                go(2)
                st.rerun()
    st.stop()

# ── ② 가치와 강점 ────────────────────────────────────────────
if stage == 2:
    d = S.pf_draft
    st.title("일할 때의 나를 조금 더 알려주세요", anchor=False)
    st.caption("고른 내용은 간이검사 결과에 반영돼요. 약 1분이면 돼요.")
    with card("pf-values", "white"):
        st.markdown("**01 · 가장 중요한 가치** · 필수")
        st.caption("중요한 순서대로 골라 주세요. 1개만 골라도 돼요.")
        prev_v = (d.get("values") or []) + [None, None, None]
        vcols = st.columns(3, gap="small")
        picks = []
        for i, col in enumerate(vcols):
            with col:
                picks.append(st.selectbox(
                    f"{i + 1}순위", profile.VALUES,
                    index=profile.VALUES.index(prev_v[i]) if prev_v[i] in profile.VALUES else None,
                    placeholder="가치를 골라 주세요", key=f"pf_value_{i}",
                ))
        values = list(dict.fromkeys(v for v in picks if v))
    st.space("small")
    with card("pf-abil-card", "white"):
        st.markdown("**02 · 자신 있는 능력** · 필수")
        abilities = st.pills(
            "잘한다고 느끼는 것을 1개에서 5개까지 골라 주세요", profile.ABILITIES,
            selection_mode="multi", default=d.get("abilities") or [], key="pf_abil",
        )
    st.space("small")
    with card("pf-trait-card", "white"):
        st.markdown("**03 · 나를 설명하는 성격** · 선택")
        traits = st.pills(
            "나와 가까운 것을 최대 3개까지 골라 주세요", profile.TRAITS,
            selection_mode="multi", default=d.get("traits") or [], key="pf_traits",
        )
    st.space("small")
    with card("pf-like-card", "white"):
        st.markdown("**04 · 좋아하는 것, 해 본 경험** · 선택")
        likes = st.text_area(
            "관심사나 기억에 남는 활동을 결과에 함께 담을 수 있어요",
            value=d.get("likes") or "",
            placeholder="예: 동아리에서 행사 기획을 맡았어요. 데이터로 근거를 찾는 게 재밌었어요.",
            max_chars=200, key="pf_likes",
        )
    test: dict = {}
    if profile.test_input_enabled():
        st.space("small")
        old = d.get("test") or {}
        with st.expander("공식 검사 결과가 있나요? 커리어넷·고용24 결과를 옮겨 적어 보세요", icon=":material/add:", expanded=bool(old)):
            st.caption(
                "입력한 흥미 유형과 가치는 간이검사 응답보다 우선 적용돼요. "
                "[커리어넷 진로심리검사](https://www.career.go.kr/cnet/front/inspct/inspctMain.do) · "
                "[고용24 직업심리검사](https://www.work24.go.kr)"
            )
            t1, t2, t3 = st.columns([1.2, 1, 1.2], gap="medium")
            with t1:
                tname = st.selectbox(
                    "검사 이름", profile.TESTS, index=profile.TESTS.index(old["name"]) if old.get("name") in profile.TESTS else None,
                    placeholder="검사를 골라 주세요", key="pf_test_name",
                )
            with t2:
                codes = st.pills(
                    "흥미 유형 상위 (최대 2개)", list(profile.RIASEC), selection_mode="multi",
                    default=old.get("riasec") or [], format_func=lambda c: profile.RIASEC[c], key="pf_test_riasec",
                )
            with t3:
                tvals = st.pills(
                    "결과의 상위 가치 (최대 3개)", profile.VALUES, selection_mode="multi",
                    default=old.get("values") or [], key="pf_test_values",
                )
            if tname and (codes or tvals):
                test = {"name": tname, "riasec": codes, "values": tvals}
    S.pf_draft = {"values": values, "abilities": list(abilities or []), "traits": list(traits or []), "likes": likes, "test": test}
    st.html(
        f'<div class="jd-progress"><span>가치 <b>{len(values)} / 3</b> · 능력 <b>{len(abilities or [])} / 5</b> · '
        f'성격 <b>{len(traits or [])} / 3</b></span></div>'
    )
    with st.container(horizontal=True, vertical_alignment="center"):
        if st.button("이전", icon=":material/arrow_back:", key="pf-prev2"):
            go(1)
            st.rerun()
        st.space("stretch")
        show = st.button("결과 보기", icon=":material/arrow_forward:", icon_position="right", type="primary", key="pf-show")
    if show:
        problems = []
        if not values:
            problems.append("중요한 가치를 하나 이상 골라 주세요")
        if not abilities:
            problems.append("자신 있는 능력을 하나 이상 골라 주세요")
        if len(abilities or []) > 5:
            problems.append(f"자신 있는 능력은 5개까지예요(지금 {len(abilities)}개)")
        if len(traits or []) > 3:
            problems.append(f"성격은 3개까지예요(지금 {len(traits)}개)")
        if test and len(test.get("riasec") or []) > 2:
            problems.append("흥미 유형은 2개까지예요")
        if test and len(test.get("values") or []) > 3:
            problems.append("결과의 상위 가치는 3개까지예요")
        pii = find_personal_info(likes)
        if pii:
            problems.append(f"{', '.join(pii)}처럼 보이는 정보는 빼 주세요")
        if problems:
            st.warning(" · ".join(problems), icon=":material/edit_note:")
            st.stop()
        answers = list(S.pf_ans)
        profile.save({
            "answers": answers, "riasec": profile.riasec_scores(answers), "values": values,
            "abilities": list(abilities), "traits": list(traits or []), "likes": likes.strip(), "test": test,
        })
        S.pf_fit_rows = None
        go(3)
        st.rerun()
    st.stop()

# ── ③ 결과 ───────────────────────────────────────────────────
p = profile.get()
if not p:
    go(1)
    st.rerun()

# ── 결과 ─────────────────────────────────────────────────────
st.space("medium")
report = st.container(key="pf-report")
ri = profile.effective_riasec(p)
top = profile.top_codes(ri, 2)
with report:
    st.html('<div class="jd-report-tag">직무 간이검사 결과지</div>')
    st.markdown(f"## 나는 **{' · '.join(profile.RIASEC[c] for c in top)}**에 가까워요")
    st.caption("아래 결과는 직무 탐색의 선배 대답, 직무 적합도, '3년 뒤의 나'에 그대로 이어져요.")
left, right = report.columns([1.1, 1], gap="medium")
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
            color=alt.Color("강조:N", scale=alt.Scale(domain=["상위", "기타"], range=["#D9F477", "#4A4C40"]), legend=None),
            tooltip=["유형", "점수"],
        )
        .properties(height=210)
        .configure_view(strokeWidth=0).configure(background="transparent")
        .configure_axis(grid=False, labelColor="#B1AFA3", domainColor="#45473B")
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
    st.markdown("**나에게 맞는 갈림길 (참고)**")
    for r in profile.recommend_path(p):
        st.progress(r["score"] / 100, text=f"{r['path']} · {r['score']}점 — {r['reason']}")

with report:
    st.space("small")
    with st.container(horizontal=True, vertical_alignment="center", key="pf-next"):
        st.markdown("**다음은 직무 탐색이에요** · 검사 결과를 바탕으로 관심 직무를 골라 AI 선배에게 일과와 준비 방법을 물어보세요.")
        if st.button("응답 수정하기", icon=":material/edit:", key="pf-edit"):
            go(1)
            st.rerun()
        if st.button("직무 탐색으로 가기", icon=":material/arrow_forward:", icon_position="right", type="primary", key="pf-go-panel"):
            st.switch_page("app_pages/panel.py")

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
                             "가치관": f["values"], "강점": f["strength"],
                             "이 직업에서 중요한 능력": ", ".join(n for n, _ in t["abilities"][:3]),
                             "채우면 좋은 능력": ", ".join(f["gaps"])})
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
