"""한국고용정보원 워크넷(고용24) 직업정보 Open API.

문서: https://www.work24.go.kr/cm/e/a/0110/selectOpenApiSvcInfo.do?fullApiSvcId=000000000000000000000000000093
- 목록: callOpenApiSvcInfo212L01.do?authKey=..&returnType=XML&target=JOBCD&srchType=K&keyword=..
- 상세: callOpenApiSvcInfo212D01.do?authKey=..&returnType=XML&target=JOBDTL&jobGb=1&jobCd=..&dtlGb=1~7
이용허락: 공공누리 제4유형(출처표시·상업적 이용금지·변경금지) → 원문을 고치지 않고 인용 근거로만 씁니다.
키(WORKNET_API_KEY)가 없거나 호출이 실패하면 None을 돌려주고, 화면은 다른 근거로 동작합니다.
"""

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


def is_enabled() -> bool:
    return get_secret("WORKNET_API_KEY") is not None


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def _get(path: str, params: tuple[tuple[str, str], ...]) -> ET.Element | None:
    key = get_secret("WORKNET_API_KEY")
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


def search_jobs(keyword: str, limit: int = 3) -> list[dict[str, str]] | None:
    root = _get("callOpenApiSvcInfo212L01.do", (("target", "JOBCD"), ("srchType", "K"), ("keyword", keyword)))
    if root is None:
        return None
    jobs = []
    for item in root.iter("jobList"):
        jobs.append({child.tag: (child.text or "").strip() for child in item})
    return jobs[:limit]


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


def summarize(job_name: str, data: dict[str, str]) -> str:
    """원문을 고치지 않고 필드별로 그대로 옮깁니다(변경금지 조건)."""
    lines = [f"직업명: {job_name}"]
    for key, label in SUMMARY_FIELDS.items():
        if data.get(key):
            lines.append(f"{label}: {data[key]}")
    if data.get("relCert"):
        lines.append(f"관련 자격: {data['relCert']}")
    if data.get("relMajor"):
        lines.append(f"관련 전공: {data['relMajor']}")
    return "\n".join(lines)
