"""한국고용정보원 워크넷(고용24) 직업정보 Open API.

문서: https://www.work24.go.kr/cm/e/a/0110/selectOpenApiSvcInfo.do?fullApiSvcId=000000000000000000000000000093
- 목록: callOpenApiSvcInfo212L01.do?authKey=..&returnType=XML&target=JOBCD&srchType=K&keyword=..
- 상세: callOpenApiSvcInfo212D01.do?authKey=..&returnType=XML&target=JOBDTL&jobGb=1&jobCd=..&dtlGb=1~7
이용허락: 공공누리 제4유형(출처표시·상업적 이용금지·변경금지) → 원문을 고치지 않고 인용 근거로만 씁니다.
키(WORKNET_API_KEY)가 없거나 호출이 실패하면 None을 돌려주고, 화면은 다른 근거로 동작합니다.
"""

import re
import xml.etree.ElementTree as ET

import requests
import streamlit as st

from utils.secrets import get_secret

BASE = "https://www.work24.go.kr/cm/openApi/call/wk"
SOURCE = "고용24 직업정보 (한국고용정보원, 공공누리 제4유형)"
# 상세구분: 1 요약, 2 하는 일, 3 교육/자격/훈련, 4 임금/만족도/전망, 5 능력/지식/환경, 6 성격/흥미/가치관, 7 업무활동
SUMMARY_FIELDS = {
    "jobSum": "하는 일",
    "way": "되는 길",
    "sal": "임금",
    "jobSatis": "직업만족도(%)",
    "jobProspect": "일자리 전망",
    "jobAbil": "업무수행능력",
}


def _key() -> str | None:
    # 고용24는 서비스마다 인증키가 다릅니다. '직업정보' 서비스 키를 씁니다(WORKNET_API_KEY는 예전 이름).
    return get_secret("WORK24_JOB_KEY") or get_secret("WORKNET_API_KEY")


def is_enabled() -> bool:
    return _key() is not None


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def _get(path: str, params: tuple[tuple[str, str], ...]) -> ET.Element | None:
    key = _key()
    if not key:
        return None
    try:
        res = requests.get(f"{BASE}/{path}", params={"authKey": key, "returnType": "XML", **dict(params)}, timeout=10)
        res.raise_for_status()
        root = ET.fromstring(res.content)
    except (requests.RequestException, ET.ParseError):
        return None
    if root.find("error") is not None or root.tag == "GO24":  # 키 미승인 등 오류 응답
        return None
    return root


def _search_once(keyword: str) -> list[dict[str, str]] | None:
    root = _get("callOpenApiSvcInfo212L01.do", (("target", "JOBCD"), ("srchType", "K"), ("keyword", keyword)))
    if root is None:
        return None
    return [{child.tag: (child.text or "").strip() for child in item} for item in root.iter("jobList")]


def _grams(text: str) -> set[str]:
    t = re.sub(r"[\s·/()]", "", text)
    return {t[i : i + 2] for i in range(len(t) - 1)}


def search_jobs(keyword: str, limit: int = 3) -> list[dict[str, str]] | None:
    """고용24 키워드 검색은 정확한 합성어(예: '게임 기획자')에 약해서,
    전체 이름 → 띄어쓰기 제거 → 낱말별로 차례로 찾아 이름이 가장 비슷한 직업을 고릅니다."""
    words = [w for w in re.split(r"[\s·/()]+", keyword) if len(w) >= 2]
    tries = [keyword, keyword.replace(" ", "")] + sorted(words, key=len, reverse=True)
    found: dict[str, dict[str, str]] = {}
    any_ok = False
    for kw in dict.fromkeys(tries):
        jobs = _search_once(kw)
        if jobs is None:
            continue
        any_ok = True
        for job in jobs:
            found.setdefault(job.get("jobCd", job.get("jobNm", "")), job)
        if len(found) >= 15:
            break
    if not any_ok:
        return None
    target = _grams(keyword)
    ranked = sorted(
        found.values(),
        key=lambda j: len(_grams(j.get("jobNm", "")) & target) / max(1, len(_grams(j.get("jobNm", "")) | target)),
        reverse=True,
    )
    best = [j for j in ranked if _grams(j.get("jobNm", "")) & target]
    return best[:limit]


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def related_jobs(keyword: str, limit: int = 5) -> list[str]:
    """고용24 직업정보의 '관련 직업' 목록(예: 사회복지사 → 심리상담전문가)."""
    found = search_jobs(keyword, limit=1)
    if not found:
        return []
    root = _get(
        "callOpenApiSvcInfo212D01.do",
        (("target", "JOBDTL"), ("jobGb", "1"), ("jobCd", found[0].get("jobCd", "")), ("dtlGb", "1")),
    )
    if root is None:
        return []
    names = [(e.text or "").strip() for e in root.findall(".//relJobList/jobNm")]
    return [n for n in dict.fromkeys(names) if n][:limit]


def job_summary(job_cd: str) -> dict[str, str] | None:
    root = _get(
        "callOpenApiSvcInfo212D01.do",
        (("target", "JOBDTL"), ("jobGb", "1"), ("jobCd", job_cd), ("dtlGb", "1")),
    )
    if root is None:
        return None
    node = root if root.tag == "jobSum" else root.find(".//jobSum")
    if node is None:
        return None
    data = {child.tag: (child.text or "").strip() for child in node if len(child) == 0}
    data["relCert"] = ", ".join((c.text or "").strip() for c in node.iter("certNm"))
    data["relMajor"] = ", ".join((m.text or "").strip() for m in node.iter("majorNm"))
    return data


def format_manwon(n: int) -> str:
    """만원 단위 숫자를 읽기 쉬운 금액으로: 10250 → '1억 250만 원', 5000 → '5,000만 원'."""
    if n >= 10000:
        eok, man = divmod(n, 10000)
        return f"{eok}억 {man:,}만 원" if man else f"{eok}억 원"
    return f"{n:,}만 원"


def readable_money(text: str) -> str:
    """'10250만원'처럼 붙은 금액 표기만 읽기 쉬운 형식으로 바꿉니다(내용·수치는 그대로)."""
    return re.sub(r"(\d[\d,]*)\s*만\s*원", lambda m: format_manwon(int(m.group(1).replace(",", ""))), text)


def summarize(job_name: str, data: dict[str, str]) -> str:
    """원문 내용은 고치지 않고 필드별로 옮깁니다(변경금지 조건). 금액은 표기만 읽기 쉽게 맞춥니다."""
    lines = [f"직업명: {job_name}"]
    for key, label in SUMMARY_FIELDS.items():
        if data.get(key):
            value = readable_money(data[key]) if key == "sal" else data[key]
            lines.append(f"{label}: {value}")
    if data.get("relCert"):
        lines.append(f"관련 자격: {data['relCert']}")
    if data.get("relMajor"):
        lines.append(f"관련 전공: {data['relMajor']}")
    return "\n".join(lines)
