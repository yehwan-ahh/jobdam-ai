"""Q-Net 국가기술자격 시험일정 (한국산업인력공단 OpenAPI).

http://openapi.q-net.or.kr/api/service/rest/InquiryTestInformationNTQSVC/{getEList|getCList|getPEList}
- getEList: 기사·산업기사, getCList: 기능사, getPEList: 기술사
- 올해 일정만 제공되므로, 다음 해 일정이 아직 없으면 '올해 일정을 참고'로 보여 줍니다.
"""

import xml.etree.ElementTree as ET
from datetime import date

import requests
import streamlit as st

from utils.cache import cache_success

from utils.secrets import get_secret

URL = "http://openapi.q-net.or.kr/api/service/rest/InquiryTestInformationNTQSVC/"
SOURCE = "Q-Net 국가기술자격 시험일정 (한국산업인력공단)"


def is_enabled() -> bool:
    return get_secret("QNET_API_KEY") is not None


# Q-Net 정기시험이 아니라 다른 기관이 따로 시행하는 자격(일정이 다름)
OTHER_BODY = {
    "빅데이터분석기사": "한국데이터산업진흥원",
    "정보보안기사": "한국인터넷진흥원",
    "정보보안산업기사": "한국인터넷진흥원",
    "컴퓨터활용능력": "대한상공회의소",
    "워드프로세서": "대한상공회의소",
    "전자상거래관리사": "대한상공회의소",
    "전자상거래운용사": "대한상공회의소",
    "리눅스마스터": "한국정보통신진흥협회",
    "데이터분석전문가": "한국데이터산업진흥원",
    "데이터분석준전문가": "한국데이터산업진흥원",
    "SQL전문가": "한국데이터산업진흥원",
}


def other_body(cert: str) -> str | None:
    return next((body for name, body in OTHER_BODY.items() if name in cert.replace(" ", "")), None)


def kind_of(cert: str) -> str | None:
    """자격 이름으로 Q-Net 시험 종류를 고릅니다. Q-Net 정기시험이 아니면 None."""
    if other_body(cert):
        return None
    if "기술사" in cert:
        return "getPEList"
    if "기사" in cert:  # 기사·산업기사
        return "getEList"
    if "기능사" in cert:
        return "getCList"
    return None


@cache_success(ttl=60 * 60 * 24)
def schedule(op: str) -> list[dict[str, str]] | None:
    key = get_secret("QNET_API_KEY")
    if not key:
        return None
    try:
        res = requests.get(URL + op, params={"serviceKey": key}, timeout=15)
        res.raise_for_status()
        root = ET.fromstring(res.content)
    except (requests.RequestException, ET.ParseError):
        return None
    rows, seen = [], set()
    for it in root.findall(".//item"):
        d = {c.tag: (c.text or "") for c in it}
        desc = d.get("description", "")
        if not desc or desc in seen or not d.get("docexamdt", "").isdigit():
            continue
        seen.add(desc)
        rows.append({
            "회차": desc,
            "필기 접수": f"{_fmt(d.get('docregstartdt'))}~{_fmt(d.get('docregenddt'))}",
            "필기 시험": _fmt(d.get("docexamdt")),
            "실기 시험": _fmt(d.get("pracexamstartdt")),
            "최종 발표": _fmt(d.get("pracpassdt")),
            "_exam": d.get("docexamdt", ""),
        })
    return rows


def _fmt(v: str | None) -> str:
    v = (v or "").strip()
    return f"{v[4:6]}.{v[6:8]}" if len(v) == 8 and v.isdigit() else "-"


def next_rounds(cert: str, n: int = 3) -> tuple[list[dict[str, str]], bool]:
    """(다가오는 회차 목록, 올해 일정 참고 여부). 다가오는 회차가 없으면 올해 일정을 참고로 돌려줍니다."""
    op = kind_of(cert)
    rows = schedule(op) if op and is_enabled() else None
    if not rows:
        return [], False
    today = date.today().strftime("%Y%m%d")
    upcoming = [r for r in rows if r["_exam"] >= today]
    if upcoming:
        return upcoming[:n], False
    return rows[:n], True
