"""Server actions for the HTML JobTalk interface."""

import re
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

import datetime as dt

import requests
import streamlit as st

from utils import careernet, company, evidence, kosis, llm, prompts, qnet, roadmap, training, worknet
from utils.secrets import get_secret
from utils.cache import cache_success

PATHS = {"취업·이직": "취업/이직", "대학원 진학": "대학원 진학", "창업": "창업"}
STARTS = [*roadmap.STARTS, "재직 중", "아직 잘 모르겠어요"]
START_PLANS = {
    "대학교 1~2학년": ["관심 전공 탐색", "기초 수업과 활동 선택", "방학 실습", "심화 전공과 결과물"],
    "대학교 3학년": ["전공 경험 정리", "인턴·연구 활동 지원", "방학 프로젝트", "졸업과 진로 전환"],
    "대학교 4학년·졸업 예정": ["졸업 일정과 마감 확인", "지원 자료 완성", "졸업 직후 계획 실행", "진입 후 성과 정리"],
    "졸업 후 준비 중": ["준비 격차 점검", "집중 실습과 지원", "결과 반영과 재지원", "경력 기반 만들기"],
    "사회초년생(1~2년 차)": ["현재 성과 정리", "업무에서 역량 검증", "전환 기회 확보", "전환 후 전문성 확장"],
    "재직 중": ["경력과 전환 조건 점검", "근무와 준비 병행", "전환 일정 확정", "새 분야의 성과 축적"],
    "아직 잘 모르겠어요": ["관심사 탐색", "작은 실험 시작", "실험 결과 비교", "방향 결정과 실행"],
}
PATH_ACTIONS = {
    "취업/이직": ["채용 공고를 비교해 핵심 역량을 정리하기", "직무 과제 하나를 포트폴리오로 만들기",
               "지원과 모의 면접 후 피드백 반영하기", "입사 후 맡은 과제와 성과를 기록하기"],
    "대학원 진학": ["연구실 두 곳의 논문과 모집 요건 읽기", "작은 연구 질문을 정하고 방법을 시험하기",
                "지도교수에게 문의하고 연구계획서 작성하기", "연구 결과를 발표 자료나 논문으로 남기기"],
    "창업": ["잠재 고객에게 문제 상황을 인터뷰하기", "작은 시제품으로 구매 의향 검증하기",
           "유료 고객을 확보하고 비용과 수익 비교하기", "재구매와 운영 지표를 바탕으로 확장 판단하기"],
}


WORK24_API = "https://www.work24.go.kr/cm/openApi/call/wk/"
RECRUIT_SOURCE = "고용24 채용정보 (한국고용정보원)"


@cache_success(ttl=900)
def recruitment(keyword):
    key = get_secret("WORK24_RECRUIT_KEY")
    if not key:
        return None
    try:
        response = requests.get(WORK24_API + "callOpenApiSvcInfo210L01.do", timeout=8, params={
            "authKey": key, "callTp": "L", "returnType": "XML",
            "startPage": 1, "display": 12, "keyword": keyword,
        })
        response.raise_for_status()
        root = ET.fromstring(response.content)
        if root.findtext("total") is None:
            return None
        return [{child.tag: (child.text or "").strip() for child in row} for row in root.iter("wanted")]
    except (requests.RequestException, ET.ParseError):
        return None


def duty_check():
    response = requests.get(WORK24_API + "callOpenApiSvcInfo215L11.do", timeout=8, params={
        "authKey": get_secret("WORK24_DUTY_KEY"), "word": "데이터", "limit": 1, "returnType": "JSON",
    })
    response.raise_for_status()
    data = response.json()
    return isinstance(data, dict) and bool(data.get("result"))


def recruitment_reply(job):
    if not job:
        return None
    rows = recruitment(job)
    if rows == [] and " " in job:
        rows = recruitment(job.split()[0])
    companies = {}
    for row in rows or []:
        name, title = row.get("company"), row.get("title")
        if name and title:
            companies.setdefault(name, row)
        if len(companies) == 3:
            break
    if not companies:
        return None
    lines, links = [], []
    for name, row in companies.items():
        details = " · ".join(filter(None, [row["title"], row.get("region"), row.get("closeDt")]))
        lines.append(f"• {name} — {details}")
        url = row.get("wantedInfoUrl", "")
        parsed = urlsplit(url)
        if parsed.scheme in {"https", "http"} and parsed.hostname in {"www.work24.go.kr", "m.work24.go.kr", "www.work.go.kr"}:
            links.append({"label": name + " 공고 보기", "url": url})
    return {"text": "고용24 검색에서 찾은 회사와 공고예요. 상세 자격 요건과 마감일은 공고에서 확인해 주세요.\n"
                    + "\n".join(lines), "sources": [RECRUIT_SOURCE], "links": links}


def _text(request, key, limit):
    value = request.get(key)
    return value.strip()[:limit] if isinstance(value, str) else ""


def chat(request):
    mode = _text(request, "mode", 12)
    job = _text(request, "job", 80)
    choice = PATHS.get(_text(request, "path", 30), "")
    question = _text(request, "question", 140)
    if not question or mode not in {"mentor", "future", "guide"}:
        return {"text": "", "label": "질문을 확인해 주세요."}
    if prompts.find_personal_info(question):
        return {"text": "", "label": "개인정보를 빼고 질문을 다시 적어 주세요."}
    history = []
    supplied = request.get("history")
    if isinstance(supplied, list):
        for message in supplied[-8:]:
            if not isinstance(message, dict):
                continue
            role = _text(message, "role", 10)
            content = _text(message, "content", 1200)
            if role in {"user", "assistant"} and content and not prompts.find_personal_info(content):
                history.append({"role": role, "content": content})
    history.append({"role": "user", "content": question})
    if not llm.is_enabled():
        return {"text": "", "label": "AI 연결 설정에서 API 키를 입력해 주세요."}
    hiring = bool(re.search(r"(회사|기업|직장|스타트업)", question) and re.search(r"(추천|어디|갈 만|알려)", question))
    listings = recruitment_reply(job) if hiring else None
    role_info, sources = evidence.job_evidence(job, question) if job else (None, [])
    if hiring:
        company_info = (listings["text"] if listings else
                        "고용24 공고 조회 결과 없음. 다른 기업 근거가 없으면 회사명을 지어내지 말고 지역과 산업을 물어봐.")
        role_info = "\n\n".join(filter(None, [role_info, company_info]))
        if listings:
            sources += listings["sources"]
    if mode == "future":
        path_info, path_sources = evidence.future_evidence(choice)
        role_info = "\n\n".join(filter(None, [role_info, path_info])) or None
        sources += path_sources
        system = prompts.future_system(choice, role_info, job)
    elif mode == "mentor":
        system = prompts.job_system(job, role_info)
    else:
        system = "너는 한국 청년의 직무 탐색을 돕는 AI 가이드야. 한국어로 짧고 자연스럽게 답하고, 관심사와 전공을 물어보며 직무를 함께 좁혀 줘. 출처와 수치를 지어내지 마."
    result = llm.generate(system, history)
    text = _clean_reply(result.text) if result.text else ""
    if text and mode != "future":  # 3년 뒤의 나는 반말 그대로
        text = prompts.polish(text)
    short = [re.sub(r"\s*\(.*?\)", "", s).strip() for s in sources]  # '고용24 직업정보 (한국고용정보원, …)' → '고용24 직업정보'
    return {"text": text,
            "label": "AI 답변" if text else (result.error or "AI 응답을 받지 못했어요. 다시 시도해 주세요."),
            "links": listings["links"] if text and listings else [],
            "sources": list(dict.fromkeys(x for x in short if x)) if text else []}


def _clean_reply(raw: str) -> str:
    """AI가 지침대로 {"answer": …, "sources": […]} JSON이나 마크다운으로 답해도, 채팅에는 대답 글만 깔끔하게."""
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text).strip()
    if text.startswith("{"):
        data = llm._parse_json(text)
        for key in ("answer", "reply", "response", "message", "대답", "답변"):
            value = data.get(key)
            if isinstance(value, dict):
                value = next((v for v in value.values() if isinstance(v, str)), "")
            if isinstance(value, list):
                value = "\n".join(str(v) for v in value)
            if isinstance(value, str) and value.strip():
                text = value.strip()
                break
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # **굵게** 표시 제거
    text = re.sub(r"(?m)^#{1,6}\s*", "", text)  # 제목 기호 제거
    text = re.sub(r"(?m)^\s*[-*]\s+", "· ", text)  # 목록 기호는 가운뎃점으로
    return text.strip()


def plan(request):
    job = _text(request, "job", 80)
    path = PATHS.get(_text(request, "path", 30))
    start = _text(request, "start", 40)
    if not job or not path or start not in STARTS:
        return {}
    if llm.is_enabled():
        try:
            result = roadmap.generate(roadmap.gather(job, path), start)
            if result.get("ai") and len(result["stages"]) == 4:
                return result
        except Exception:
            pass
    return {
        "stages": [
            {"title": title, "period": period, "goals": [f"{start} 상황에서 {job} 준비"],
             "actions": [action]}
            for title, period, action in zip(START_PLANS[start], roadmap.STAGES, PATH_ACTIONS[path])
        ],
        "checkpoint": f"{path} 경로에서 {job} 관련 성과를 쌓고 다음 목표를 정하기",
        "ai": False,
    }


def connections():
    return {
        "ai": ("AI · " + llm.provider_label(), llm.is_enabled,
               lambda: bool(llm.generate("너는 연결 점검 도구야. OK 한 단어만 답해.", [{"role": "user", "content": "OK"}]).text)),
        "careernet": ("커리어넷", careernet.is_enabled, lambda: careernet.search_jobs("간호사", 1)),
        "worknet": ("고용24 직업정보", worknet.is_enabled, lambda: worknet.search_jobs("간호사", 1)),
        "recruit": ("고용24 채용정보", lambda: bool(get_secret("WORK24_RECRUIT_KEY")), lambda: recruitment("간호사") is not None),
        "duty": ("고용24 직무정보", lambda: bool(get_secret("WORK24_DUTY_KEY")), duty_check),
        "training": ("고용24 훈련과정", training.is_enabled, lambda: training.courses("엑셀", limit=1)),
        "kosis": ("KOSIS", kosis.is_enabled, lambda: kosis.fetch("startup_survival_by_industry", 1) is not None),
        "qnet": ("Q-Net", qnet.is_enabled, lambda: qnet.schedule("getEList")),
        "companies": ("고용24 청년친화강소기업", lambda: bool(get_secret("WORK24_SMALLGIANT_KEY")), company.smallgiants),
        "dart": ("DART 기업공시", lambda: bool(get_secret("DART_API_KEY")), company.dart_corps),
        "nps": ("국민연금 사업장", lambda: bool(get_secret("NPS_API_KEY")), lambda: company.nps_info("삼성전자")),
    }


def connection_list():
    return [{"key": key, "label": name, "configured": bool(enabled())}
            for key, (name, enabled, _) in connections().items()]


def check(request):
    service = connections().get(_text(request, "service", 20))
    if not service or not service[1]():
        return {"status": "미설정"}
    try:
        ok = bool(service[2]())
    except Exception:
        ok = False
    return {"status": "연결 확인" if ok else "응답 확인 실패"}


def _date(v: str) -> str:
    """'20261201'·'2026-12-01'·'2026.12.01' → '2026-12-01' (화면이 오늘 날짜와 비교해요)."""
    d = re.sub(r"[^0-9]", "", v or "")
    return f"{d[:4]}-{d[4:6]}-{d[6:8]}" if len(d) >= 8 else ""


def resource(request):
    """로드맵 카드의 '국비 교육'(고용24 훈련과정)·'관련 자격'(Q-Net 시험일정) 공개 정보."""
    kind, key = _text(request, "kind", 20), _text(request, "key", 60)
    now = dt.datetime.now().isoformat(timespec="seconds")
    if not key:
        return {"status": "unavailable"}
    if kind == "training":
        rows = training.courses(key, limit=3) if training.is_enabled() else None
        if rows is None:
            return {"status": "unavailable"}
        return {"status": "ok", "checkedAt": now, "rows": [
            {"title": r["title"], "provider": r.get("org", ""), "area": r.get("area", ""),
             "start": _date(r.get("start", "")), "end": _date(r.get("end", "")),
             "url": r["link"] if r.get("link", "").startswith("https://www.work24.go.kr/") else ""}
            for r in rows]}
    if kind == "certificate":
        if not qnet.is_enabled() or not qnet.kind_of(key):
            return {"status": "ok", "checkedAt": now, "rows": []}
        rows, past = qnet.next_rounds(key, 1)
        if not rows:
            return {"status": "ok", "checkedAt": now, "rows": []}
        r = rows[0]
        return {"status": "ongoing", "checkedAt": now, "source": "https://www.q-net.or.kr/",
                "apply": f"{r['회차']} 필기 {r['필기 접수']}" + (" (올해 일정 참고)" if past else ""),
                "exam": f"필기 {r['필기 시험']} · 실기 {r['실기 시험']}"}
    return {"status": "unavailable"}


def byok(request):
    """'API 연결 상태'에서 넣은 내 API 키. 이 접속(세션)에만 두고 저장·기록하지 않아요."""
    st.session_state[llm.BYOK_STATE_KEY] = _text(request, "key", 300)
    return {"status": "저장됨" if st.session_state[llm.BYOK_STATE_KEY] else "지움"}


def dispatch(request):
    action = {"chat": chat, "plan": plan, "check": check, "resource": resource, "byok": byok}.get(_text(request, "action", 12))
    return action(request) if action else {}
