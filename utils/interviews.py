"""직업 인터뷰(커리어넷 '진로 솔루션 · 직업 솔로몬') 검색.

- 원문 폴더: data/interviews/*.txt  (이용 조건 확인 전까지 .gitignore로 GitHub에 올리지 않음)
- 학습이 아니라 검색(RAG)용: 질문과 관련된 문단을 찾아 AI 근거로 넘기고 출처를 표시합니다.
- 개인정보 보호: 인터뷰이·선생님 실명은 '현직자'·'선생님'으로 바꾸고 직함·소속만 남깁니다.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import streamlit as st

FOLDER = Path(__file__).resolve().parent.parent / "data" / "interviews"
SOURCE = "커리어넷 진로 솔루션(직업 솔로몬) 인터뷰"
CHUNK = 450  # 문단 묶음 크기(자)


@dataclass(frozen=True)
class Passage:
    job: str
    issue: str
    text: str


def is_enabled() -> bool:
    return FOLDER.is_dir() and any(FOLDER.glob("*.txt"))


def _job_name(path: Path) -> str:
    name = re.sub(r"^\d+_", "", path.stem)
    return re.sub(r"\s*\(\d+\)$", "", name).strip()


def _scrub_names(text: str) -> str:
    """'홍길동 님', '홍길동 선생님', 표지의 '홍길동 (소속)'으로 나온 이름을 모아 문서 전체에서 지웁니다."""
    names = set(re.findall(r"([가-힣]{2,4})\s*(?:님|선생님)(?![가-힣])", text))
    cover = text.split("## 2쪽")[0]
    names |= set(re.findall(r"(?:^|[\s|])([가-힣]{2,3})\s*\(\s*[^)\n]{2,40}\)", cover))
    names -= {"선생", "학생", "교수", "부모", "고객", "여러분", "친구"}
    for name in sorted(names, key=len, reverse=True):
        text = re.sub(rf"{name}\s*선생님", "선생님", text)
        text = re.sub(rf"{name}\s*님", "현직자", text)
        text = text.replace(name, "OOO")
    return text


def _clean(text: str) -> str:
    lines = []
    for line in text.splitlines():
        s = line.strip().strip("|").strip()
        if not s or s.startswith("# ") or re.fullmatch(r"##\s*\d+쪽", s) or re.fullmatch(r"\d{1,3}", s):
            continue
        lines.append(s)
    joined = " ".join(lines)
    return re.sub(r"\s{2,}", " ", joined)


@st.cache_data(show_spinner=False)
def load() -> list[Passage]:
    passages: list[Passage] = []
    if not is_enabled():
        return passages
    for path in sorted(FOLDER.glob("*.txt")):
        raw = path.read_text(encoding="utf-8-sig", errors="ignore")
        m = re.search(r"진로\s*솔루션\s*(\d{4})\s*\.?\s*vol\s*\.?\s*(\d+)", raw, re.IGNORECASE) or re.search(
            r"Solution\s*Paper[\s\d]*?(20\d{2})\s*Vol\s*\.?\s*(\d+)", raw, re.IGNORECASE
        )
        issue = f"{m.group(1)} vol.{int(m.group(2)):02d}" if m else ""
        # 표지(1쪽)는 목차·이름 목록이라 빼고 2쪽부터 씁니다.
        body = _clean(_scrub_names(raw).split("## 2쪽", 1)[-1])
        # 질문(Q1, Q2 …) 경계를 우선으로 자르고, 길면 CHUNK 단위로 다시 자릅니다.
        parts = re.split(r"(?=Q\d{1,2}\s)", body)
        for part in parts:
            for i in range(0, len(part), CHUNK):
                piece = part[i : i + CHUNK].strip()
                if len(piece) > 80:
                    passages.append(Passage(_job_name(path), issue, piece))
    return passages


def _bigrams(text: str) -> set[str]:
    t = re.sub(r"\s+", "", text)
    return {t[i : i + 2] for i in range(len(t) - 1)}


def jobs() -> list[str]:
    return sorted({p.job for p in load()})


def search(question: str, roles: list[str], k: int = 3) -> list[Passage]:
    """질문과 직무(역할) 이름에 가장 가까운 인터뷰 문단 k개."""
    passages = load()
    if not passages:
        return []
    role_grams = [_bigrams(r) for r in roles]
    q_grams = _bigrams(question)

    def job_score(job: str) -> float:
        g = _bigrams(job)
        return max((len(g & rg) / max(1, len(g | rg)) for rg in role_grams), default=0.0)

    matched_jobs = {j for j in {p.job for p in passages} if job_score(j) >= 0.25}
    if not matched_jobs:
        return []
    scored = []
    for p in passages:
        if p.job not in matched_jobs:
            continue
        g = _bigrams(p.text)
        scored.append((len(g & q_grams) + 5 * job_score(p.job), p))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:k]]


def evidence(question: str, roles: list[str]) -> tuple[str | None, str | None]:
    hits = search(question, roles)
    if not hits:
        return None, None
    text = "\n".join(f"[진로 솔루션 인터뷰 · {p.job}{' · ' + p.issue if p.issue else ''}] {p.text}" for p in hits)
    issues = sorted({f"{p.job} ({p.issue})" if p.issue else p.job for p in hits})
    return text, f"{SOURCE}: " + ", ".join(issues)
