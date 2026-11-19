"""AI 시대 새 직업 카드(data/new_jobs.json).

공공 직업분류에 아직 없는 직업이라 연봉·전망 숫자는 쓰지 않고, related(가장 가까운 고용24 직업)의
공공데이터로 연결합니다. 설명(하는 일·준비 방법)은 생성형 AI로 초안을 쓴 뒤 다듬은 큐레이션입니다.
"""

import json
from pathlib import Path

import streamlit as st

PATH = Path(__file__).resolve().parent.parent / "data" / "new_jobs.json"
SOURCE = "잡담 새 직업 카드(큐레이션 · 공공 통계 없음)"


@st.cache_data(show_spinner=False)
def _load(mtime: float) -> list[dict]:
    del mtime
    return json.loads(PATH.read_text(encoding="utf-8")).get("jobs", [])


def jobs() -> list[dict]:
    try:
        return _load(PATH.stat().st_mtime)
    except (OSError, ValueError):
        return []


def names() -> list[str]:
    return [j["name"] for j in jobs()]


def get(name: str | None) -> dict | None:
    if not name:
        return None
    key = name.replace(" ", "")
    return next((j for j in jobs() if j["name"].replace(" ", "") == key or j.get("en", "").replace(" ", "").lower() == key.lower()), None)


def related(name: str) -> str:
    """새 직업이면 가장 가까운 고용24 직업, 아니면 그대로."""
    card = get(name)
    return card["related"] if card else name


def categories() -> list[str]:
    return list(dict.fromkeys(j["category"] for j in jobs()))


def all_domains() -> list[str]:
    return sorted({d for j in jobs() for d in j.get("domains", [])})


def all_skills() -> list[str]:
    return sorted({s for j in jobs() for s in j.get("skills", [])})


def evidence(name: str) -> str | None:
    card = get(name)
    if not card:
        return None
    lines = [
        f"[{SOURCE} · {card['name']}]",
        f"- 정의: {card['one_line']}",
        "- 하는 일: " + " / ".join(card["duties"]),
        "- 필요한 역량: " + ", ".join(card["skills"]),
        "- 준비 방법: " + " / ".join(card["prepare"]),
    ]
    if card.get("sources"):
        lines.append("- 실제 채용·보도 사례: " + " / ".join(s["title"] for s in card["sources"]))
    else:
        lines.append("- 국내 채용 사례는 아직 확인하지 못한 신흥 직무예요.")
    lines.append(
        f"- 이 직업은 공공 직업분류에 아직 없어요. 연봉·전망 같은 숫자는 가장 가까운 공공 직업 '{card['related']}'의 "
        "고용24 근거로만 말하고, 반드시 '관련 직업 기준'이라고 밝혀요."
    )
    return "\n".join(lines)


def match(domains: list[str], skills: list[str]) -> list[tuple[dict, int]]:
    """융합 커리어 찾기: 내 도메인·역량과 겹치는 정도로 정렬."""
    my_s = [s.lower() for s in skills]
    scored = []
    for j in jobs():
        d = len(set(domains) & set(j.get("domains", [])))
        s = sum(1 for k in j.get("skills", []) if any(m in k.lower() or k.lower() in m for m in my_s))
        if d or s:
            scored.append((j, d * 2 + s))
    return sorted(scored, key=lambda x: -x[1])
