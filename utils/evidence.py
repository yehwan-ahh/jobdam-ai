"""AI에 넘길 근거자료 모으기."""

import streamlit as st

from utils import careernet, kosis


def panel_evidence(roles: list[str]) -> tuple[str | None, list[str]]:
    """직무별 커리어넷 정보를 모읍니다. (근거 텍스트, 찾은 직업명 목록)"""
    if not careernet.is_enabled():
        return None, []
    chunks: list[str] = []
    found: list[str] = []
    for role in roles:
        jobs = careernet.search_jobs(role, limit=1)
        if not jobs:
            continue
        job = jobs[0]
        detail = careernet.job_detail(job.get("job_cd") or job.get("seq") or "")
        if detail:
            chunks.append(f"[커리어넷 · {role}]\n{careernet.summarize_detail(detail)}")
            found.append(str(job.get("job_nm", role)))
        elif job.get("work"):
            chunks.append(f"[커리어넷 · {role}]\n직업명: {job.get('job_nm')}\n하는 일: {job.get('work')}")
            found.append(str(job.get("job_nm", role)))
    return ("\n\n".join(chunks) or None), found


def future_evidence(choice: str) -> tuple[str | None, list[str]]:
    """갈림길별 KOSIS 통계를 표 형태 텍스트로. (근거 텍스트, 사용한 통계표 제목)"""
    if not kosis.is_enabled():
        return None, []
    chunks: list[str] = []
    used: list[str] = []
    for key in kosis.FUTURE_TABLES.get(choice, []):
        df = kosis.fetch(key)
        table = kosis.TABLES[key]
        if df is None or df.empty:
            continue
        sample = df.head(30).to_csv(index=False)
        chunks.append(f"[KOSIS · {table.title} · {table.source}]\n{sample}")
        used.append(table.title)
    return ("\n\n".join(chunks) or None), used


def show_sources(names: list[str], label: str) -> None:
    if names:
        st.caption(f":material/link: 근거: {label} — " + ", ".join(names))
