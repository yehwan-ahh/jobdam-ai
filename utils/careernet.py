"""커리어넷 직업정보 Open API (한국직업능력연구원, 공공누리 제1유형).

문서: https://www.career.go.kr/cnet/front/openapi/jobCenter.do
- 목록: /cnet/front/openapi/jobs.json?apiKey=..&searchJobNm=..&pageIndex=..
- 상세: /cnet/front/openapi/job.json?apiKey=..&seq=<job_cd>
키(CAREERNET_API_KEY)가 없거나 호출이 실패하면 None을 돌려주고, 화면은 시연 모드로 동작합니다.
"""

from typing import Any

import requests
import streamlit as st

from utils.cache import cache_success

from utils.secrets import get_secret

BASE = "https://www.career.go.kr/cnet/front/openapi"
SOURCE = "한국직업능력연구원 커리어넷 직업정보 (공공누리 제1유형)"
SOURCE_URL = "https://www.career.go.kr/cnet/front/base/job/jobList.do"


def is_enabled() -> bool:
    return get_secret("CAREERNET_API_KEY") is not None


@cache_success(ttl=60 * 60 * 24)
def _get(path: str, params: tuple[tuple[str, str], ...]) -> dict[str, Any] | None:
    key = get_secret("CAREERNET_API_KEY")
    if not key:
        return None
    try:
        res = requests.get(f"{BASE}/{path}", params={"apiKey": key, **dict(params)}, timeout=10)
        res.raise_for_status()
        return res.json()
    except (requests.RequestException, ValueError):
        return None


def search_jobs(keyword: str, limit: int = 5) -> list[dict[str, Any]] | None:
    """직업명 검색. [{job_cd, job_nm, work, wage, ...}] 또는 None."""
    data = _get("jobs.json", (("searchJobNm", keyword), ("pageIndex", "1")))
    if data is None:
        return None
    return list(data.get("jobs") or [])[:limit]


def job_detail(seq: str | int) -> dict[str, Any] | None:
    return _get("job.json", (("seq", str(seq)),))


def summarize_detail(detail: dict[str, Any]) -> str:
    """LLM에 근거로 넘길 짧은 텍스트. 원문 필드만 옮기고 해석하지 않습니다."""
    base = detail.get("baseInfo") or {}
    lines = [f"직업명: {base.get('job_nm', '')}"]
    works = [w.get("work", "") for w in detail.get("workList") or []]
    if works:
        lines.append("하는 일: " + " / ".join(works[:5]))
    abilities = [a.get("ability_name", "") for a in detail.get("abilityList") or [] if a.get("ability_name")]
    if abilities:
        lines.append("핵심 능력: " + ", ".join(abilities[:6]))
    ready = detail.get("jobReadyList") or {}
    if isinstance(ready, dict):
        for k, label in (("recruit", "입직·채용"), ("certificate", "관련 자격"), ("training", "훈련")):
            items = [str(i.get(k, "")) for i in ready.get(k) or [] if isinstance(i, dict)]
            if items:
                lines.append(f"{label}: " + " / ".join(items[:3]))
    forecasts = [f.get("forecast", "") for f in detail.get("forecastList") or []]
    if forecasts:
        lines.append("전망: " + " ".join(forecasts[:2]))
    if base.get("wage"):
        lines.append(f"임금(커리어넷 표기): {base.get('wage')}")
    return "\n".join(line for line in lines if line.strip())
