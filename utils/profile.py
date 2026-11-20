"""내 프로필(간이 흥미 체크 + 공식 검사 결과 입력)과 공공데이터 기반 직업 적합도.

- 프로필은 이 세션(st.session_state)에만 있고 서버·파일에 저장하지 않습니다.
- '공식 검사 결과 입력' 칸은 Secrets의 PROFILE_TEST_INPUT="off"로 언제든 숨길 수 있습니다.
- 적합도는 고용24 직업정보에 직업마다 들어 있는 흥미(Holland)·가치관·능력·성격 점수와
  사용자가 고른 성향을 비교한 '참고 지표'입니다. 공식 심리검사가 아닙니다.
"""

import re

import streamlit as st

from utils import new_jobs, worknet
from utils.secrets import get_secret

STATE = "profile"

RIASEC = {"R": "현실형", "I": "탐구형", "A": "예술형", "S": "사회형", "E": "진취형", "C": "관습형"}
RIASEC_DESC = {
    "R": "손으로 만들고 현장에서 움직이는 일",
    "I": "원리를 파고들고 분석하는 일",
    "A": "아이디어를 표현하고 새로 만드는 일",
    "S": "사람을 돕고 가르치는 일",
    "E": "사람을 이끌고 성과를 키우는 일",
    "C": "정리하고 절차대로 정확히 처리하는 일",
}
ITEMS = [
    ("R", "기계·도구를 직접 다루거나 무언가를 만들 때 즐거워요"),
    ("I", "원리를 파고들어 분석하는 게 재미있어요"),
    ("A", "아이디어를 글·그림·영상으로 표현하는 게 좋아요"),
    ("S", "사람을 돕거나 가르칠 때 보람을 느껴요"),
    ("E", "사람들을 이끌고 설득하는 게 좋아요"),
    ("C", "자료를 꼼꼼히 정리하고 관리하는 게 편해요"),
    ("R", "책상보다 현장에서 몸을 움직이며 일하고 싶어요"),
    ("I", "데이터나 실험으로 답을 찾는 게 좋아요"),
    ("A", "정해진 틀보다 자유롭게 만드는 게 편해요"),
    ("S", "다른 사람 이야기를 잘 들어 주는 편이에요"),
    ("E", "목표를 세우고 성과를 키우는 데 끌려요"),
    ("C", "규칙과 절차대로 정확히 처리하는 게 좋아요"),
]
SCALE = ["전혀 아니에요", "아닌 편", "보통", "그런 편", "매우 그래요"]

# 고용24 직업정보에서 쓰는 이름 그대로(비교를 위해)
VALUES = ["경제적 보상", "직업안정", "일과 삶의 균형", "자기개발", "성취", "자율성", "변화지향", "사회적 인정", "사회적 공헌"]
ABILITIES = [
    "논리적 분석", "추리력", "수리력", "전산", "문제 해결", "판단과 의사결정", "창의력", "글쓰기", "말하기",
    "듣고 이해하기", "설득", "협상", "가르치기", "사람 파악", "서비스 지향", "시간 관리", "학습전략",
    "기술 분석", "기술 설계", "품질관리분석", "재정 관리", "인적자원 관리", "공간지각력",
]
TRAITS = [
    "분석적 사고", "혁신", "꼼꼼함", "신뢰성", "성취/노력", "적응성/융통성", "협조", "리더십", "인내",
    "독립성", "사회성", "타인에 대한 배려", "정직성", "책임과 진취성", "자기통제", "스트레스 감내성",
]
TESTS = ["커리어넷 직업가치관검사", "커리어넷 직업흥미검사", "고용24 직업선호도검사", "기타 검사"]
TEST_LINKS = {
    "커리어넷 진로심리검사": "https://www.career.go.kr/cnet/front/inspct/inspctMain.do",
    "고용24 직업심리검사": "https://www.work24.go.kr",
}


def test_input_enabled() -> bool:
    return (get_secret("PROFILE_TEST_INPUT") or "on").lower() not in ("off", "false", "0", "no")


def get() -> dict | None:
    p = st.session_state.get(STATE)
    return p if isinstance(p, dict) and p.get("riasec") else None


def save(data: dict) -> None:
    st.session_state[STATE] = data


def clear() -> None:
    st.session_state.pop(STATE, None)


# ── 성향 계산 ────────────────────────────────────────────────
def riasec_scores(answers: list[str]) -> dict[str, int]:
    """12문항(유형당 2개)의 5점 응답 → 유형별 0~100."""
    acc: dict[str, list[int]] = {k: [] for k in RIASEC}
    for (code, _), ans in zip(ITEMS, answers):
        acc[code].append(SCALE.index(ans) if ans in SCALE else 2)
    return {k: round(sum(v) / (4 * len(v)) * 100) if v else 50 for k, v in acc.items()}


def effective_riasec(p: dict) -> dict[str, int]:
    """공식 검사의 흥미 유형을 입력했다면 그걸 우선합니다."""
    test = (p.get("test") or {}) if test_input_enabled() else {}
    codes = test.get("riasec") or []
    if codes:
        base = {k: 30 for k in RIASEC}
        for rank, c in enumerate(codes):
            base[c] = 100 - rank * 15
        return base
    return p["riasec"]


def effective_values(p: dict) -> list[str]:
    test = (p.get("test") or {}) if test_input_enabled() else {}
    return test.get("values") or p.get("values") or []


def top_codes(scores: dict[str, int], n: int = 3) -> list[str]:
    return [k for k, _ in sorted(scores.items(), key=lambda kv: -kv[1])[:n]]


# ── 고용24 직업 성향 점수 ─────────────────────────────────────
_PAIR = re.compile(r"(.*?)\((\d+)\)/?")
_INT_CODE = {"현실형": "R", "탐구형": "I", "예술형": "A", "사회형": "S", "진취형": "E", "관습형": "C"}


def _parse(text: str | None) -> list[tuple[str, int]]:
    if not text:
        return []
    return [(n.strip(), int(s)) for n, s in _PAIR.findall(text) if n.strip()]


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def job_traits(job: str) -> dict | None:
    """고용24 직업정보의 흥미·가치관·능력·성격 점수. 못 찾으면 None."""
    if not worknet.is_enabled():
        return None
    card = new_jobs.get(job)
    found = worknet.search_jobs(card["related"] if card else job, limit=1)
    if not found:
        return None
    root = worknet._get(
        "callOpenApiSvcInfo212D01.do",
        (("target", "JOBDTL"), ("jobGb", "1"), ("jobCd", found[0]["jobCd"]), ("dtlGb", "1")),
    )
    if root is None:
        return None

    def field(tag: str) -> str | None:
        el = root.find(f".//{tag}")
        return el.text if el is not None else None

    interest = []
    for name, score in _parse(field("jobIntrst")):
        code = next((c for k, c in _INT_CODE.items() if name.startswith(k)), None)
        if code:
            interest.append((code, score))
    return {
        "name": found[0].get("jobNm", job) + (" · 새 직업의 가장 가까운 공공 직업 기준" if card else ""),
        "interest": interest,
        "values": _parse(field("jobVals")),
        "abilities": _parse(field("jobAbil")),
        "traits": _parse(field("jobChr")),
        "certs": [c.strip() for c in (field("certNm") or "").split(",") if c.strip()],
    }


def fit(p: dict, t: dict) -> dict:
    """프로필과 직업 성향 점수 비교 → 0~100 적합도와 이유."""
    ri = effective_riasec(p)
    if t["interest"]:
        w = sum(s for _, s in t["interest"])
        interest = sum(s * ri.get(c, 50) for c, s in t["interest"]) / w
    else:
        interest = 50
    job_vals = dict(t["values"])
    my_vals = effective_values(p)
    weights = [1.0, 0.8, 0.6]
    if my_vals:
        values = sum(weights[i] * job_vals.get(v, 40) for i, v in enumerate(my_vals[:3])) / sum(weights[: len(my_vals[:3])])
    else:
        values = 50
    job_strength = dict(t["abilities"] + t["traits"])
    mine = (p.get("abilities") or []) + (p.get("traits") or [])
    strength = sum(job_strength.get(x, 40) for x in mine) / len(mine) if mine else 50
    total = round(0.4 * interest + 0.35 * values + 0.25 * strength)
    match = [x for x in my_vals if x in job_vals] + [x for x in mine if x in job_strength]
    gaps = [n for n, _ in t["abilities"][:5] if n not in mine][:3]
    return {
        "total": total, "interest": round(interest), "values": round(values), "strength": round(strength),
        "match": match, "gaps": gaps,
    }


# ── 갈림길(취업·대학원·창업) 추천 ─────────────────────────────
# 흥미 유형(Holland)과 가치관이 각 길에서 얼마나 쓰이는지에 대한 일반적인 경향으로 만든 참고 규칙입니다.
PATH_RULES = {
    "취업/이직": {"types": {"C": 1.0, "S": 0.8, "R": 0.8, "E": 0.5}, "values": ["직업안정", "일과 삶의 균형", "경제적 보상", "사회적 인정"],
               "why": "정해진 조직 안에서 역할을 맡아 경력과 소득을 차근차근 쌓는 길"},
    "대학원 진학": {"types": {"I": 1.0, "A": 0.6, "S": 0.3}, "values": ["자기개발", "성취", "자율성"],
                "why": "한 분야를 깊게 파고들어 전문성을 키우는 길"},
    "창업": {"types": {"E": 1.0, "A": 0.7, "R": 0.3}, "values": ["자율성", "변화지향", "성취", "경제적 보상"],
           "why": "스스로 문제를 정하고 사람을 모아 새 일을 만드는 길"},
}


def recommend_path(p: dict) -> list[dict]:
    """간이검사 결과로 세 갈림길의 맞는 정도(0~100)와 이유. 높은 순."""
    ri = effective_riasec(p)
    vals = effective_values(p)[:3]
    weights = [1.0, 0.8, 0.6]
    out = []
    for path, rule in PATH_RULES.items():
        t = sum(w * ri.get(c, 50) for c, w in rule["types"].items()) / sum(rule["types"].values())
        if vals:
            v = sum(weights[i] for i, x in enumerate(vals) if x in rule["values"]) / sum(weights[: len(vals)]) * 100
        else:
            v = 50
        score = round(0.6 * t + 0.4 * v)
        top_types = [RIASEC[c] for c in sorted(rule["types"], key=lambda c: -ri.get(c, 0)) if ri.get(c, 0) >= 60][:2]
        hit_vals = [x for x in vals if x in rule["values"]]
        reason = []
        if top_types:
            reason.append(f"{'·'.join(top_types)} 흥미가 높고")
        if hit_vals:
            reason.append(f"'{', '.join(hit_vals)}'을(를) 중요하게 여겨요")
        out.append({"path": path, "score": score, "reason": " ".join(reason) or "흥미·가치관이 고르게 걸쳐 있어요", "about": rule["why"]})
    return sorted(out, key=lambda r: -r["score"])


# ── AI 프롬프트용 요약 ────────────────────────────────────────
def prompt_block(job: str | None = None) -> str:
    p = get()
    if not p:
        return ""
    ri = effective_riasec(p)
    lines = ["<사용자 프로필> (사용자가 직접 고른 참고 정보이며 공식 검사 결과가 아닐 수 있음)"]
    lines.append("- 흥미 유형: " + ", ".join(f"{RIASEC[c]} {ri[c]}" for c in top_codes(ri)))
    if effective_values(p):
        lines.append("- 일할 때 중요한 가치(순서대로): " + ", ".join(effective_values(p)))
    if p.get("abilities"):
        lines.append("- 스스로 꼽은 강점: " + ", ".join(p["abilities"]))
    if p.get("traits"):
        lines.append("- 나를 설명하는 성격: " + ", ".join(p["traits"]))
    if p.get("likes"):
        lines.append(f"- 좋아하는 것·해 본 경험: {p['likes']}")
    test = p.get("test") or {}
    if test_input_enabled() and (test.get("riasec") or test.get("values")):
        lines.append(f"- 공식 검사 결과(사용자 입력): {test.get('name', '')}")
    if job:
        t = job_traits(job)
        if t:
            f = fit(p, t)
            lines.append(
                f"- '{job}' 적합도(참고 지표, 고용24 직업 성향 점수와 비교): {f['total']}점 "
                f"(흥미 {f['interest']}, 가치관 {f['values']}, 강점 {f['strength']})"
            )
            if f["match"]:
                lines.append("  · 잘 맞는 점: " + ", ".join(f["match"]))
            if f["gaps"]:
                lines.append("  · 이 직무에서 중요한데 아직 고르지 않은 능력: " + ", ".join(f["gaps"]))
    rec = recommend_path(p)
    lines.append("- 간이검사 기준 잘 맞는 갈림길(참고): " + ", ".join(f"{r['path']} {r['score']}" for r in rec))
    lines.append(
        "활용 규칙: 이 프로필로 답을 그 사람에게 맞게 구체화합니다(예: \"분석을 좋아한다면\"). "
        "사람을 단정하지 않고, 프로필에 없는 개인 사실을 지어내지 않습니다. 적합도를 말할 때는 참고 지표라고 밝힙니다."
    )
    lines.append("</사용자 프로필>")
    return "\n".join(lines)


# ── 화면 조각 ────────────────────────────────────────────────
def summary_line(p: dict) -> str:
    ri = effective_riasec(p)
    code = "".join(top_codes(ri, 2))
    vals = effective_values(p)[:2]
    return f"{' · '.join(RIASEC[c] for c in code)}" + (f" | 중요한 가치: {', '.join(vals)}" if vals else "")


def render_fit(job: str, key: str) -> None:
    """선택 직무와 내 프로필의 적합도 카드(프로필이 있을 때만)."""
    p = get()
    if not p:
        st.caption(":material/person: '직무 간이검사'를 하면 이 직무와 나의 적합도를 공공데이터로 보여 줘요.")
        return
    t = job_traits(job)
    if not t:
        st.caption(":material/info: 이 직무는 고용24 성향 점수가 없어 적합도를 계산하지 못했어요.")
        return
    f = fit(p, t)
    with st.container(horizontal=True, vertical_alignment="center", key=f"fit-{key}"):
        st.metric("나와의 적합도", f"{f['total']}점", border=True, width="content")
        st.metric("흥미", f["interest"], border=True, width="content")
        st.metric("가치관", f["values"], border=True, width="content")
        st.metric("강점", f["strength"], border=True, width="content")
    mine = set((p.get("abilities") or []) + (p.get("traits") or []))
    key_abil = t["abilities"][:5]
    if key_abil:
        chips = " · ".join(f"{'✓ ' if n in mine else ''}{n} {s}" for n, s in key_abil)
        st.markdown(f"**이 직업에서 중요한 능력** · {chips}")
        st.caption("숫자는 고용24가 매긴 이 직업의 능력 중요도(0~100)예요. ✓는 내가 간이검사에서 고른 능력이에요.")
    if f["match"]:
        st.markdown("**잘 맞는 점** · " + ", ".join(f["match"]))
    if f["gaps"]:
        st.markdown("**채우면 좋은 능력** · " + ", ".join(f["gaps"]))
    if f["strength"] < 50 and key_abil:
        st.caption(
            ":material/lightbulb: '강점' 점수는 내가 고른 능력이 이 직업의 중요한 능력과 얼마나 겹치는지로 계산해요. "
            "위 능력을 키우거나 이미 갖췄다면 간이검사에서 골라 보세요."
        )
    st.caption(
        f":material/link: 고용24 직업정보 '{t['name']}'의 흥미·가치관·능력 점수와 내 간이검사 결과를 비교한 참고 지표예요. 공식 검사가 아니에요."
    )
