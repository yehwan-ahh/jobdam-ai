"""AI에 넘길 근거자료 모으기. 출처별로 [출처 · 항목] 머리말을 붙여 AI가 출처를 표시할 수 있게 합니다."""

import streamlit as st

from utils import careernet, interviews, kosis, majors, new_jobs, training, worknet


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
                chunks.append(f"[고용24 · {role}에 가장 가까운 직업 정보]\n{text}")
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
        # 원자료 표 대신 미리 정리한 핵심 숫자만 넘겨 응답을 빠르고 정확하게 합니다.
        from utils import compare

        summary = compare.stats(choice)
        if summary.evidence:
            chunks.append(summary.evidence)
            sources.append(f"KOSIS ({summary.source})")
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
    card = new_jobs.get(job)  # AI 시대 새 직업이면 카드 + 가장 가까운 공공 직업으로
    public = card["related"] if card else job
    if card:
        chunks.append(new_jobs.evidence(job) or "")
        sources.append(new_jobs.SOURCE)
    if careernet.is_enabled():
        text = _careernet(public)
        if text:
            chunks.append(f"[커리어넷 · {public}]\n{text}")
            sources.append(careernet.SOURCE)
    if worknet.is_enabled():
        text = _worknet(public)
        if text:
            label = (f"'{job}'과 가장 가까운 공공 직업 '{public}' 정보 (숫자는 이 관련 직업 기준이라고 밝힘)" if card
                     else f"{job}에 가장 가까운 직업 정보 (직업명이 다르면 '관련 직업'으로 소개)")
            chunks.append(f"[고용24 · {label}]\n{text}")
            sources.append(worknet.SOURCE)
    if training.is_enabled():
        text = training.evidence(card["keywords"][0] if card else job)
        if text:
            chunks.append(text)
            sources.append(training.SOURCE)
    if interviews.is_enabled():
        text, label = interviews.evidence(question or job, [job])
        if text and label:
            chunks.append(text)
            sources.append(label)
    major_line = majors.evidence(major)
    if major_line:
        chunks.append(major_line)
        sources.append(majors.SOURCE)
    co_text, co_sources = company_evidence(question, job)
    if co_text:
        chunks.append(co_text)
        sources += co_sources
    return ("\n\n".join(chunks) or None), sources


def company_evidence(question: str, job: str) -> tuple[str | None, list[str]]:
    """질문에 회사 이야기가 있으면 강소기업·국민연금·DART 근거(없으면 None). 실패해도 채팅은 계속돼요."""
    if not question:
        return None, []
    from utils import company

    try:
        return company.evidence(question, job)
    except Exception:
        return None, []


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
    names += new_jobs.names()  # AI 시대 새 직업 카드
    seen: set[str] = set()
    return [n for n in names if not (n in seen or seen.add(n))]
