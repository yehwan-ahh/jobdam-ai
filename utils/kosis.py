"""KOSIS 국가통계포털 OpenAPI (통계자료 - 파라미터 방식).

문서: https://kosis.kr/openapi/devGuide/devGuide_0201List.do
요청: https://kosis.kr/openapi/Param/statisticsParameterData.do?method=getList
      &apiKey=..&orgId=..&tblId=..&itmId=..&objL1=..&prdSe=Y&newEstPrdCnt=..&format=json&jsonVD=Y
키(KOSIS_API_KEY)가 없거나 호출이 실패하면 None을 돌려주고, 화면은 시연 모드로 동작합니다.

아래 TABLES의 orgId/tblId는 2026-11-17 KOSIS 검색 화면에서 확인한 값입니다.
itmId·objL 코드는 표마다 달라서, 키 발급 후 메타 조회로 확정해야 합니다(confirmed=False).
"""

from dataclasses import dataclass, field
from typing import Any

import pandas as pd
import requests
import streamlit as st

from utils.secrets import get_secret

URL = "https://kosis.kr/openapi/Param/statisticsParameterData.do"


@dataclass(frozen=True)
class KosisTable:
    org_id: str
    tbl_id: str
    title: str
    source: str
    years: str
    params: dict[str, str] = field(default_factory=dict)  # itmId, objL1.. 등 (확정 전에는 ALL)
    confirmed: bool = False

    @property
    def url(self) -> str:
        return f"https://kosis.kr/statHtml/statHtml.do?orgId={self.org_id}&tblId={self.tbl_id}"


TABLES: dict[str, KosisTable] = {
    # 창업 — 기업생멸행정통계(국가데이터처)
    "startup_survival_by_industry": KosisTable(
        "101", "DT_2BD1103", "산업별 신생기업 생존율", "국가데이터처, 기업생멸행정통계", "2012~2024"
    ),
    "startup_survival_by_ceo_age": KosisTable(
        "101", "DT_2BD1104", "대표자 성·연령별 신생기업 생존율", "국가데이터처, 기업생멸행정통계", "2012~2024"
    ),
    # 취업/이직 — 일자리이동통계(국가데이터처)
    "job_mobility_by_age": KosisTable(
        "101", "DT_1JTJ_A001", "성별·연령별 일자리 이동", "국가데이터처, 일자리이동통계", "2017~2024"
    ),
    "job_mobility_by_firm_size": KosisTable(
        "101", "DT_1JTJ_A011", "연령별·기업규모별 일자리 이동", "국가데이터처, 일자리이동통계", "2017~2024"
    ),
    # 임금 — 고용형태별근로실태조사(고용노동부)
    "wage_by_education_age": KosisTable(
        "118", "DT_118N_PAY0004", "규모·학력·연령계층·성별 임금 및 근로조건", "고용노동부, 고용형태별노동실태조사", "2009~2025"
    ),
    # 대학원 진학 — 고등교육기관 졸업자 취업통계(한국교육개발원)
    "grad_employment_by_field": KosisTable(
        "334", "DT_33403N_005", "계열별 졸업상황", "한국교육개발원, 교육기관 졸업자 취업통계", "확인 필요"
    ),
}

# 갈림길별로 보여 줄 통계
FUTURE_TABLES: dict[str, list[str]] = {
    "취업/이직": ["job_mobility_by_age", "wage_by_education_age"],
    "대학원 진학": ["grad_employment_by_field", "wage_by_education_age"],
    "창업": ["startup_survival_by_industry", "startup_survival_by_ceo_age"],
}


def is_enabled() -> bool:
    return get_secret("KOSIS_API_KEY") is not None


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def fetch(table_key: str, recent_periods: int = 3) -> pd.DataFrame | None:
    """통계표를 DataFrame으로. 키가 없거나 실패하면 None (숫자를 지어내지 않습니다)."""
    key = get_secret("KOSIS_API_KEY")
    table = TABLES.get(table_key)
    if not key or table is None:
        return None
    params = {
        "method": "getList",
        "apiKey": key,
        "orgId": table.org_id,
        "tblId": table.tbl_id,
        "itmId": "ALL",
        "objL1": "ALL",
        "prdSe": "Y",
        "newEstPrdCnt": str(recent_periods),
        "format": "json",
        "jsonVD": "Y",
        **table.params,
    }
    try:
        res = requests.get(URL, params=params, timeout=15)
        res.raise_for_status()
        data: Any = res.json()
    except (requests.RequestException, ValueError):
        return None
    if not isinstance(data, list) or not data:  # 오류 응답은 {"err": "..", "errMsg": ".."} 형태
        return None
    df = pd.DataFrame(data)
    keep = [c for c in ("PRD_DE", "C1_NM", "C2_NM", "ITM_NM", "DT", "UNIT_NM") if c in df.columns]
    df = df[keep].copy()
    if "DT" in df.columns:
        df["DT"] = pd.to_numeric(df["DT"], errors="coerce")
    return df
