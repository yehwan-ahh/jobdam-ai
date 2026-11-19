"""고용24 국민내일배움카드 훈련과정 (구 HRD-Net) Open API.

문서: https://www.work24.go.kr/cm/e/a/0110/selectOpenApiSvcInfo.do?fullApiSvcId=000000000000000000000000000004
요청: /cm/openApi/call/hr/callOpenApiSvcInfo310L01.do?authKey=..&returnType=JSON&outType=1&pageNum=1&pageSize=..
      &srchTraStDt=YYYYMMDD&srchTraEndDt=YYYYMMDD&srchTraProcessNm=과정명&sort=DESC&sortCol=5(만족도)
키(WORK24_TRAINING_KEY)가 없으면 None → 화면에서 자동으로 숨깁니다.
"""

import datetime as dt
import re
from typing import Any

import requests
import streamlit as st

from utils.secrets import get_secret

URL = "https://www.work24.go.kr/cm/openApi/call/hr/callOpenApiSvcInfo310L01.do"
SOURCE = "고용24 국민내일배움카드 훈련과정"


def is_enabled() -> bool:
    return get_secret("WORK24_TRAINING_KEY") is not None


@st.cache_data(ttl=60 * 60 * 6, show_spinner=False)
def _search(keyword: str, days: int = 120, size: int = 20) -> list[dict[str, Any]] | None:
    key = get_secret("WORK24_TRAINING_KEY")
    if not key:
        return None
    today = dt.date.today()
    params = {
        "authKey": key,
        "returnType": "JSON",
        "outType": "1",
        "pageNum": "1",
        "pageSize": str(size),
        "srchTraStDt": today.strftime("%Y%m%d"),
        "srchTraEndDt": (today + dt.timedelta(days=days)).strftime("%Y%m%d"),
        "srchTraProcessNm": keyword,
        "sort": "DESC",
        "sortCol": "5",  # 만족도 점수
    }
    try:
        res = requests.get(URL, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()
    except (requests.RequestException, ValueError):
        return None
    items = data.get("srchList") if isinstance(data, dict) else None
    return list(items) if isinstance(items, list) else []


def _keywords(job: str) -> list[str]:
    """직무명에서 과정명 검색어를 만듭니다. 예: '데이터 분석가' → ['데이터 분석', '데이터', '분석']"""
    base = re.sub(r"\(.*?\)", "", job).strip()
    stem = re.sub(r"(전문가|개발자|엔지니어|디자이너|기획자|분석가|연구원|관리자|사무원|코디네이터|리서처|프로그래머|공무원|사)$", "", base).strip()
    words = [w for w in re.split(r"[\s·/]+", stem) if len(w) >= 2]
    tries = [stem, base] + sorted(words, key=len, reverse=True)
    return [t for t in dict.fromkeys(tries) if len(t) >= 2]


def courses(job: str, limit: int = 3) -> list[dict[str, str]] | None:
    """선택한 직무를 준비할 수 있는 다가오는 훈련과정(만족도 높은 순)."""
    if not is_enabled():
        return None
    picked: dict[str, dict[str, str]] = {}
    for kw in _keywords(job):
        items = _search(kw)
        if items is None:
            return None
        for it in items:
            pid = f"{it.get('trprId')}-{it.get('trprDegr')}"
            if pid not in picked:
                picked[pid] = {
                    "title": str(it.get("title", "")).strip(),
                    "org": str(it.get("subTitle", "")).strip(),
                    "start": str(it.get("traStartDate", "")),
                    "end": str(it.get("traEndDate", "")),
                    "fee": str(it.get("realMan", "")),
                    "area": str(it.get("address", "")).strip(),
                    "target": str(it.get("trainTarget", "")).strip(),
                    "link": str(it.get("titleLink", "")),
                }
        if len(picked) >= limit:
            break
    return list(picked.values())[:limit]


def evidence(job: str) -> str | None:
    items = courses(job)
    if not items:
        return None
    lines = [f"- {c['title']} ({c['org']}, {c['start']}~{c['end']}, {c['area']})" for c in items]
    return f"[{SOURCE} · {job} 관련 다가오는 국비 지원 과정]\n" + "\n".join(lines)


def render(job: str) -> None:
    """직무 화면에 보여 줄 훈련과정 카드 목록."""
    items = courses(job)
    if items is None:
        return
    st.markdown("#### 이 직무를 준비할 국비 지원 교육과정")
    if not items:
        st.caption("지금부터 4개월 안에 시작하는 관련 과정을 찾지 못했어요. 고용24에서 직접 검색해 보세요.")
        return
    for c in items:
        with st.container(border=True):
            st.markdown(f"**[{c['title']}]({c['link']})**" if c["link"] else f"**{c['title']}**")
            fee = f" · 훈련비 {int(c['fee']):,}원" if c["fee"].isdigit() else ""
            st.caption(f"{c['org']} · {c['area']} · {c['start']} ~ {c['end']}{fee} · {c['target']}")
    st.caption(f":material/link: 출처: {SOURCE} (원문에서 자부담·지원 조건을 꼭 확인하세요)")
