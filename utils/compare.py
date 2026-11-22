"""갈림길(취업·대학원·창업) 비교: KOSIS 실제 값으로 숫자 카드·차트·짧은 근거 문장을 만듭니다.

숫자는 KOSIS 응답에 있는 값만 씁니다. 비율을 계산한 경우(이동자 ÷ 전체)는 라벨에 '계산'이라고 밝힙니다.
불러오지 못하면 None을 돌려주고, 화면은 '아직 불러오지 못했어요'로 안내합니다.
"""

from dataclasses import dataclass, field

import altair as alt
import pandas as pd

from utils import kosis

BLACK, GRAY = "#D9F477", "#5A5C4E"


@dataclass
class PathStats:
    metrics: list[tuple[str, str]] = field(default_factory=list)  # (라벨, 값)
    chart: alt.Chart | None = None
    caption: str = ""  # 차트 설명
    source: str = ""  # 출처·기준 연도
    evidence: str = ""  # AI에 넘길 짧은 근거 문장
    error: str | None = None


def _pct(v: float | None) -> str:
    return "-" if v is None or pd.isna(v) else f"{v:.1f}%"


def _bar(df: pd.DataFrame, x: str, y: str, color_field: str, highlight: str, y_title: str, sort: list[str]) -> alt.Chart:
    return (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X(f"{x}:N", sort=sort, title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y(f"{y}:Q", title=y_title),
            xOffset=alt.XOffset(f"{color_field}:N") if color_field != x else alt.value(0),
            color=alt.Color(
                f"{color_field}:N",
                scale=alt.Scale(range=[BLACK, GRAY], domain=[highlight, *[v for v in df[color_field].unique() if v != highlight]]),
                legend=alt.Legend(orient="bottom", title=None) if color_field != x else None,
            ),
            tooltip=[x, color_field, alt.Tooltip(f"{y}:Q", format=",.1f")] if color_field != x else [x, alt.Tooltip(f"{y}:Q", format=",.1f")],
        )
        .properties(height=190)
        .configure_view(strokeWidth=0).configure(background="transparent")
        .configure_axis(grid=False, labelColor="#B1AFA3", titleColor="#B1AFA3", domainColor="#45473B")
    )


def startup() -> PathStats:
    t = kosis.TABLES["startup_survival_by_ceo_age"]
    df, err = kosis.raw("startup_survival_by_ceo_age")
    if df is None:
        return PathStats(error=err)
    year = str(df["PRD_DE"].max())
    df = df[df["PRD_DE"] == year]
    df = df.assign(기간=df["ITM_NM"].str.replace(" 생존율", "", regex=False), 연령=df["C2_NM"])
    youth = df[df["연령"] == "30대 미만"].set_index("기간")["DT"]
    total = df[df["연령"] == "계"].set_index("기간")["DT"]
    chart_df = df[df["연령"].isin(["30대 미만", "계"])].assign(
        구분=lambda d: d["연령"].map({"30대 미만": "30대 미만 대표", "계": "전체"})
    )
    order = ["1년", "2년", "3년", "4년", "5년"]
    return PathStats(
        metrics=[("30대 미만 대표, 3년 생존율", _pct(youth.get("3년"))), ("전체 창업, 3년 생존율", _pct(total.get("3년")))],
        chart=_bar(chart_df, "기간", "DT", "구분", "30대 미만 대표", "생존율(%)", order),
        caption="창업 후 해마다 살아남은 기업 비율",
        source=f"{year}년 · {t.source}",
        evidence=(
            f"[KOSIS · {t.title} · {year}년 기준] 30대 미만 대표 생존율: "
            + ", ".join(f"{k} {_pct(youth.get(k))}" for k in order)
            + " / 전체: "
            + ", ".join(f"{k} {_pct(total.get(k))}" for k in order)
        ),
    )


def job() -> PathStats:
    w = kosis.TABLES["wage_by_education_age"]
    df, err = kosis.raw("wage_by_education_age")
    if df is None:
        return PathStats(error=err)
    year = str(df["PRD_DE"].max())
    df = df[(df["PRD_DE"] == year) & (df["C2_NM"].isin(["대졸이상", "고졸"]))]
    ages = ["20 ~ 24", "25 ~ 29", "30 ~ 34", "35 ~ 39", "40 ~ 44"]
    df = df[df["C4_NM"].isin(ages)].assign(
        만원=lambda d: d["DT"] / 10, 연령=lambda d: d["C4_NM"].str.replace(" ", "", regex=False), 학력=lambda d: d["C2_NM"]
    )
    grad = df[df["학력"] == "대졸이상"].set_index("연령")["만원"]
    metrics = [("대졸 이상 25~29세, 월 임금", f"{grad.get('25~29', float('nan')):,.0f}만 원")]
    evidence = (
        f"[KOSIS · {w.title} · {year}년 기준] 대졸이상 월임금총액: "
        + ", ".join(f"{a}세 {v:,.0f}만 원" for a, v in grad.items())
    )
    # 청년(15~29세) 1년 내 일자리 이동 비율 (이동자 ÷ 전체, 계산)
    m, _ = kosis.raw("job_mobility_by_age")
    if m is not None:
        my = str(m["PRD_DE"].max())
        y = m[(m["PRD_DE"] == my) & (m["C3_NM"] == "15-29세")].set_index("C4_NM")["DT"]
        if y.get("총계") and y.get("이동자") is not None:
            rate = y["이동자"] / y["총계"] * 100
            metrics.append(("15~29세, 1년 안에 일자리 옮긴 비율(계산)", _pct(rate)))
            evidence += f"\n[KOSIS · 일자리이동통계 · {my}년 기준] 15~29세 근로자 중 1년 안에 일자리를 옮긴 사람 비율 {_pct(rate)} (이동자 ÷ 전체로 계산)"
    return PathStats(
        metrics=metrics,
        chart=_bar(df, "연령", "만원", "학력", "대졸이상", "월 임금(만 원)", [a.replace(" ", "") for a in ages]),
        caption="나이대별 월 임금총액 (전규모·전체 성별)",
        source=f"{year}년 · {w.source}",
        evidence=evidence,
    )


def grad() -> PathStats:
    t = kosis.TABLES["grad_employment_by_field"]
    df, err = kosis.raw("grad_employment_by_field")
    if df is None:
        return PathStats(error=err)
    year = str(df["PRD_DE"].max())
    df = df[(df["PRD_DE"] == year) & (df["C2_NM"] == "취업률")]
    top = {"15334HGP0004": "대학", "15334HGP0008": "일반대학원"}
    totals = df[df["C1"].isin(top)].assign(학제=lambda d: d["C1"].map(top)).set_index("학제")["DT"]
    fields = ["인문계열", "사회계열", "공학계열", "자연계열", "예체능계열"]
    rows = []
    for code, label in top.items():
        sub = df[df["C1"].str.startswith(code) & (df["C1"] != code) & df["C1_NM"].isin(fields)]
        rows += [{"계열": r["C1_NM"].replace("계열", ""), "학제": label, "취업률": r["DT"]} for _, r in sub.iterrows()]
    chart_df = pd.DataFrame(rows)
    chart = (
        _bar(chart_df, "계열", "취업률", "학제", "일반대학원", "취업률(%)", [f.replace("계열", "") for f in fields])
        if not chart_df.empty
        else None
    )
    return PathStats(
        metrics=[("일반대학원 졸업자 취업률", _pct(totals.get("일반대학원"))), ("대학(학부) 졸업자 취업률", _pct(totals.get("대학")))],
        chart=chart,
        caption="계열별 졸업자 취업률",
        source=f"{year}년 · {t.source}",
        evidence=(
            f"[KOSIS · {t.title} · {year}년 기준] 취업률: 일반대학원 {_pct(totals.get('일반대학원'))}, "
            f"대학(학부) {_pct(totals.get('대학'))}; 계열별 "
            + ", ".join(f"{r['학제']} {r['계열']} {_pct(r['취업률'])}" for r in rows)
        ),
    )


BUILDERS = {"취업/이직": job, "대학원 진학": grad, "창업": startup}


def stats(choice: str) -> PathStats:
    try:
        return BUILDERS[choice]()
    except Exception as e:  # noqa: BLE001 — 표 구조가 바뀌어도 화면은 살립니다
        return PathStats(error=f"통계를 정리하지 못했어요 ({type(e).__name__})")
