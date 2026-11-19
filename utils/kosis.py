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
    params: dict[str, str] = field(default_factory=dict)  # itmId, objL1.. 직접 지정 (비우면 메타로 자동 결정)
    item_keywords: tuple[str, ...] = ()  # 자동 결정 시 먼저 고를 항목명 키워드
    all_level: int = 1  # 자동 결정 시 전체(ALL)로 펼칠 분류 단계
    confirmed: bool = False

    @property
    def url(self) -> str:
        return f"https://kosis.kr/statHtml/statHtml.do?orgId={self.org_id}&tblId={self.tbl_id}"


TABLES: dict[str, KosisTable] = {
    # 창업 — 기업생멸행정통계(국가데이터처)
    "startup_survival_by_industry": KosisTable(
        "101", "DT_2BD1103", "산업별 신생기업 생존율", "국가데이터처, 기업생멸행정통계", "2012~2024",
        params={"itmId": "T01+T03+T05+", "objL1": "ALL"}, confirmed=True,
    ),
    "startup_survival_by_ceo_age": KosisTable(
        "101", "DT_2BD1104", "대표자 성·연령별 신생기업 생존율", "국가데이터처, 기업생멸행정통계", "2012~2024",
        params={"itmId": "T01+T02+T03+T04+T05+", "objL1": "0", "objL2": "ALL"}, confirmed=True,
    ),
    # 취업/이직 — 일자리이동통계(국가데이터처)
    "job_mobility_by_age": KosisTable(
        "101", "DT_1JTJ_A001", "성별·연령별 일자리 이동", "국가데이터처, 일자리이동통계", "2017~2024",
        # 기간(1년내 이동) · 성별(총계) · 연령(전체) · 이동유형(전체)
        params={"itmId": "T1+", "objL1": "01", "objL2": "00", "objL3": "ALL", "objL4": "ALL"}, confirmed=True,
    ),
    "job_mobility_by_firm_size": KosisTable(
        "101", "DT_1JTJ_A011", "연령별·기업규모별 일자리 이동", "국가데이터처, 일자리이동통계", "2017~2024",
        # 기간(1년내 이동) · 연령(15-29세) · 기업규모(전체) · 이동유형(전체)
        params={"itmId": "T1+", "objL1": "01", "objL2": "01", "objL3": "ALL", "objL4": "ALL"}, confirmed=True,
    ),
    # 임금 — 고용형태별근로실태조사(고용노동부)
    "wage_by_education_age": KosisTable(
        "118", "DT_118N_PAY0004", "규모·학력·연령계층·성별 임금 및 근로조건", "고용노동부, 고용형태별노동실태조사", "2009~2025",
        # 월임금총액 · 규모(전규모) · 학력(전체) · 성별(전체) · 연령(전체)
        params={"itmId": "16118DD_10+", "objL1": "13102205067SIZES.00", "objL2": "ALL",
                "objL3": "13102205067SEXS.0", "objL4": "ALL"}, confirmed=True,
    ),
    # 대학원 진학 — 고등교육기관 졸업자 취업통계(한국교육개발원)
    "grad_employment_by_field": KosisTable(
        "334", "DT_33403N_005", "계열별 졸업상황", "한국교육개발원, 교육기관 졸업자 취업통계", "최근 3년",
        # 학제·계열(전체) · 졸업상황(취업률, 진학률)
        params={"itmId": "ABC005+", "objL1": "ALL", "objL2": "15334HGS002009+15334HGS00200A+"}, confirmed=True,
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


META_URL = "https://kosis.kr/openapi/statisticsData.do"
COLUMN_NAMES = {"PRD_DE": "연도", "C1_NM": "구분1", "C2_NM": "구분2", "C3_NM": "구분3", "ITM_NM": "항목", "DT": "값", "UNIT_NM": "단위"}
MAX_ITEMS = 4  # 한 번에 가져올 항목 수 (KOSIS 한 번 호출당 4만 셀 제한)


def _get_json(url: str, params: dict[str, str]) -> tuple[Any, str | None]:
    try:
        res = requests.get(url, params=params, timeout=20)
        res.raise_for_status()
        data: Any = res.json()
    except requests.RequestException:
        return None, "KOSIS 서버에 연결하지 못했어요."
    except ValueError:
        return None, "KOSIS 응답을 읽지 못했어요."
    if isinstance(data, dict) and data.get("err"):
        return None, f"KOSIS 오류 {data.get('err')}: {data.get('errMsg', '')}"
    return data, None


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def _auto_params(
    org_id: str, tbl_id: str, item_keywords: tuple[str, ...] = (), all_level: int = 1
) -> tuple[dict[str, str] | None, str | None]:
    """통계표 메타(항목·분류)를 읽어 조회 코드를 정합니다.
    항목은 앞에서 최대 4개, 첫 분류는 전체(ALL), 나머지 분류는 최상위 첫 값(대개 '계')."""
    key = get_secret("KOSIS_API_KEY")
    meta, err = _get_json(
        META_URL,
        {"method": "getMeta", "type": "ITM", "apiKey": key or "", "orgId": org_id, "tblId": tbl_id,
         "format": "json", "jsonVD": "Y"},
    )
    if err or not isinstance(meta, list) or not meta:
        return None, err or "통계표 구조(메타)를 찾지 못했어요."
    item_rows = [m for m in meta if m.get("OBJ_ID") == "ITEM"]
    preferred = [m for m in item_rows if any(k in str(m.get("ITM_NM", "")) for k in item_keywords)]
    rest = [m for m in item_rows if m not in preferred]
    items = [m["ITM_ID"] for m in (preferred + rest)][:MAX_ITEMS]
    if not items:
        return None, "항목 코드를 찾지 못했어요."
    params = {"itmId": "+".join(items) + "+"}
    objs: dict[str, list[dict[str, Any]]] = {}
    for m in meta:
        if m.get("OBJ_ID") != "ITEM":
            objs.setdefault(str(m.get("OBJ_ID")), []).append(m)
    ordered = sorted(objs.values(), key=lambda rows: int(rows[0].get("OBJ_ID_SN") or 99))
    for level, rows in enumerate(ordered[:8], start=1):
        if level == all_level:
            params[f"objL{level}"] = "ALL"
        else:
            top = [r for r in rows if not r.get("UP_ITM_ID")] or rows
            params[f"objL{level}"] = str(top[0]["ITM_ID"])
    return params, None


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def load(table_key: str, recent_periods: int = 3) -> tuple[pd.DataFrame | None, str | None]:
    """통계표를 (DataFrame, 오류 안내)로. 실패하면 DataFrame은 None (숫자를 지어내지 않습니다)."""
    key = get_secret("KOSIS_API_KEY")
    table = TABLES.get(table_key)
    if not key or table is None:
        return None, "KOSIS 키가 없어요."
    params = dict(table.params)
    if not params:
        params, err = _auto_params(table.org_id, table.tbl_id, table.item_keywords, table.all_level)
        if params is None:
            return None, err
    query = {
        "method": "getList",
        "apiKey": key,
        "orgId": table.org_id,
        "tblId": table.tbl_id,
        "prdSe": "Y",
        "newEstPrdCnt": str(recent_periods),
        "format": "json",
        "jsonVD": "Y",
        **params,
    }
    data, err = _get_json(URL, query)
    if err or not isinstance(data, list) or not data:
        return None, err or "조회 결과가 비어 있어요."
    df = pd.DataFrame(data)
    keep = [c for c in ("PRD_DE", "C1_NM", "C2_NM", "C3_NM", "ITM_NM", "DT", "UNIT_NM") if c in df.columns]
    df = df[keep].copy()
    if "DT" in df.columns:
        df["DT"] = pd.to_numeric(df["DT"], errors="coerce")
    df = df.rename(columns=COLUMN_NAMES)
    return df, None


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def raw(table_key: str, recent_periods: int = 1) -> tuple[pd.DataFrame | None, str | None]:
    """코드(C1, ITM_ID 등)까지 담은 원자료. 비교 그래프처럼 행을 정확히 골라야 할 때 씁니다."""
    key = get_secret("KOSIS_API_KEY")
    table = TABLES.get(table_key)
    if not key or table is None or not table.params:
        return None, "KOSIS 키가 없어요."
    query = {"method": "getList", "apiKey": key, "orgId": table.org_id, "tblId": table.tbl_id, "prdSe": "Y",
             "newEstPrdCnt": str(recent_periods), "format": "json", "jsonVD": "Y", **table.params}
    data, err = _get_json(URL, query)
    if err or not isinstance(data, list) or not data:
        return None, err or "조회 결과가 비어 있어요."
    df = pd.DataFrame(data)
    df["DT"] = pd.to_numeric(df.get("DT"), errors="coerce")
    return df, None


def fetch(table_key: str, recent_periods: int = 3) -> pd.DataFrame | None:
    return load(table_key, recent_periods)[0]
