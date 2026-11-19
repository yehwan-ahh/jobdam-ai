"""AI에 넘길 근거자료 모으기. 출처별로 [출처 · 항목] 머리말을 붙여 AI가 출처를 표시할 수 있게 합니다."""

import streamlit as st

from utils import careernet, interviews, kosis, majors, worknet


def _careernet(role: str) -> str | None:
    jobs = careernet.search_jobs(role, limit=1)
    if not jobs:
        return None
    job = jobs[0]
    detail = careernet.job_detail(job.get("job_cd") or job.get("seq") or "")
    if detail:
        return careernet.summarize_detail(detail)
    if job.get("work"):
        return f"직업명: {job.get('job_nm')}\n하는 일: {job.get('work')}"
    return None


def _worknet(role: str) -> str | None:
    jobs = worknet.search_jobs(role, limit=1)
    if not jobs:
        return None
    job = jobs[0]
    data = worknet.job_summary(job.get("jobCd", ""))
    return worknet.summarize(job.get("jobNm", role), data) if data else None


def panel_evidence(
    roles: list[str], major: str | None = None, question: str = "", field: str = ""
) -> tuple[str | None, list[str]]:
    """직무별 공공 직업정보 + (선택) 학과 상위 진출 직업. (근거 텍스트, 사용한 출처 목록)"""
    chunks: list[str] = []
    sources: list[str] = []
    for role in roles:
        if careernet.is_enabled():
            text = _careernet(role)
            if text:
                chunks.append(f"[커리어넷 · {role}]\n{text}")
                if careernet.SOURCE not in sources:
                    sources.append(careernet.SOURCE)
        if worknet.is_enabled():
            text = _worknet(role)
            if text:
                chunks.append(f"[고용24 · {role}]\n{text}")
                if worknet.SOURCE not in sources:
                    sources.append(worknet.SOURCE)
    if interviews.is_enabled():
        text, label = interviews.evidence(question, [field, *roles] if field else roles)
        if text and label:
            chunks.append(text)
            sources.append(label)
    major_line = majors.evidence(major)
    if major_line:
        chunks.append(major_line)
        sources.append(majors.SOURCE)
    return ("\n\n".join(chunks) or None), sources


def future_evidence(choice: str, major: str | None = None) -> tuple[str | None, list[str]]:
    """갈림길별 KOSIS 통계 + (선택) 학과 상위 진출 직업. (근거 텍스트, 사용한 출처 목록)"""
    chunks: list[str] = []
    sources: list[str] = []
    if kosis.is_enabled():
        for key in kosis.FUTURE_TABLES.get(choice, []):
            df = kosis.fetch(key)
            table = kosis.TABLES[key]
            if df is None or df.empty:
                continue
            chunks.append(f"[KOSIS · {table.title} · {table.source}]\n{df.head(30).to_csv(index=False)}")
            sources.append(f"KOSIS {table.title}")
    major_line = majors.evidence(major)
    if major_line:
        chunks.append(major_line)
        sources.append(majors.SOURCE)
    return ("\n\n".join(chunks) or None), sources


def show_sources(names: list[str]) -> None:
    if names:
        st.caption(":material/link: 근거: " + " · ".join(names))


def job_evidence(job: str, question: str = "", major: str | None = None) -> tuple[str | None, list[str]]:
    """선택한 직무 하나에 대한 근거(커리어넷·고용24·현직자 인터뷰·학과)."""
    chunks: list[str] = []
    sources: list[str] = []
    if careernet.is_enabled():
        text = _careernet(job)
        if text:
            chunks.append(f"[커리어넷 · {job}]\n{text}")
            sources.append(careernet.SOURCE)
    if worknet.is_enabled():
        text = _worknet(job)
        if text:
            chunks.append(f"[고용24 · {job}]\n{text}")
            sources.append(worknet.SOURCE)
    if interviews.is_enabled():
        text, label = interviews.evidence(question or job, [job])
        if text and label:
            chunks.append(text)
            sources.append(label)
    major_line = majors.evidence(major)
    if major_line:
        chunks.append(major_line)
        sources.append(majors.SOURCE)
    return ("\n\n".join(chunks) or None), sources


def recommend_candidates(major: str | None = None) -> list[str]:
    """추천 후보: 학과 상위 진출 직업 + 현직자 인터뷰 직업 + 잡담 기본 패널 직무 + 상위진출직업 데이터의 전체 직업."""
    from utils.demo_data import PANELS

    names: list[str] = []
    if major:
        names += majors.top_jobs(major)
    if interviews.is_enabled():
        names += interviews.jobs()
    for personas in PANELS.values():
        names += [p["role"] for p in personas]
    names += sorted(majors.load()["직업분류명"].unique().tolist())  # 상위진출직업 데이터의 직업 146개
    seen: set[str] = set()
    return [n for n in names if not (n in seen or seen.add(n))]
