"""회사 정보: 채팅에서 회사를 물으면 공공데이터로 간단히 소개합니다.

- 고용24 청년친화강소기업 (WORK24_SMALLGIANT_KEY): 업종·지역·주요 제품·상시 근로자·선정 브랜드
- 국민연금 가입 사업장 (NPS_API_KEY, 공공데이터포털): 가입자(직원) 수, 이번 달 입사·퇴사
- 금융감독원 DART (DART_API_KEY): 기업 개요, 직원 수·평균 근속·1인 평균 급여, 매출·영업이익

키가 없거나 호출이 실패하면 그 부분만 빠지고, 채팅은 그대로 동작합니다.
회사 이름은 공공데이터에서 실제로 찾은 회사만 근거로 넘깁니다(지어낸 회사 방지).
"""

import io
import re
import zipfile
import xml.etree.ElementTree as ET
from datetime import date

import requests

from utils.cache import cache_success
from utils.secrets import get_secret

SG_SOURCE = "고용24 청년친화강소기업(고용노동부)"
NPS_SOURCE = "국민연금 가입 사업장 내역(국민연금공단)"
DART_SOURCE = "DART 전자공시(금융감독원)"

SG_URL = "https://www.work24.go.kr/cm/openApi/call/wk/callOpenApiSvcInfo216L01.do"
NPS_URL = "https://apis.data.go.kr/B552015/NpsBplcInfoInqireServiceV2/"
DART_URL = "https://opendart.fss.or.kr/api/"
SEOUL = "11000"

# 회사 이야기인지 알아보는 말
_COMPANY_WORDS = re.compile(r"회사|기업|직장|입사|다니|취업처|근무 ?환경|복지|평균 ?연봉")  # 분명한 회사 이야기
_RECO = re.compile(
    r"(어떤|어느|무슨|추천|갈 ?만한|괜찮은|좋은|관련|대표)\s*(회사|기업|곳|직장)|(회사|기업)\s*(추천|예시|목록|있|어디)|어디(서|에)\s*(일|취업|근무)"
)
_PARTICLES = ("이라는", "에서는", "이라고", "에서", "으로", "이랑", "에는", "라는", "라고", "이란", "은", "는", "이", "가", "을", "를", "에", "의", "랑", "과", "와", "도", "로", "란")
_VERBISH = re.compile(r"(요|다|까|해|줘|죠|네|나|지|어|게|고|면|서|니)$")  # 동사·형용사로 끝나는 말은 회사 이름 후보에서 빼요
_STOP = {
    "회사", "기업", "직장", "직무", "신입", "연봉", "정도", "어때요", "어때", "어떤", "어느", "무슨", "추천", "괜찮은", "좋은",
    "관련", "대표", "다니기", "다니면", "입사", "취업", "근무", "복지", "분위기", "선배", "저", "제가", "나", "내가", "요즘",
    "그", "이", "거기", "여기", "정말", "진짜", "혹시", "평균", "월급", "보수", "일하기", "곳", "어디", "어디서", "어디에",
}

# 직무 이름의 단어 → 관련 업종(한국표준산업분류 대분류)
_INDUSTRY = [
    (r"개발|소프트웨어|프로그래|데이터|AI|인공지능|웹|앱|보안|네트워크|게임|클라우드|엔지니어|IT|정보", ["J"]),
    (r"마케팅|광고|홍보|기획|콘텐츠|디자인|UX|UI|브랜드|PD|방송|영상|출판|기자", ["J", "M"]),
    (r"회계|재무|세무|금융|은행|보험|투자|증권", ["K", "M"]),
    (r"인사|총무|사무|경영|영업|무역|유통|판매|MD|구매|물류", ["G", "H", "M"]),
    (r"기계|전기|전자|반도체|화학|생산|품질|제조|설비|자동차|소재|공정", ["C"]),
    (r"건축|토목|건설|인테리어|설계", ["F", "M"]),
    (r"연구|분석|컨설턴트|변리|연구원", ["M"]),
    (r"간호|의료|보건|사회복지|요양|상담", ["Q"]),
    (r"교사|교육|강사|교수", ["P"]),
]


def _sg_key() -> str | None:
    return get_secret("WORK24_SMALLGIANT_KEY")


def _nps_key() -> str | None:
    return get_secret("NPS_API_KEY")


def _dart_key() -> str | None:
    return get_secret("DART_API_KEY")


def is_enabled() -> bool:
    return bool(_sg_key() or _nps_key() or _dart_key())


def norm(name: str) -> str:
    """회사 이름 비교용: (주)·주식회사·띄어쓰기를 빼고 소문자로."""
    n = re.sub(r"\(주\)|㈜|주식회사|\(유\)|유한회사|\(재\)|재단법인|\(사\)|사단법인|\s", "", name or "")
    return n.lower()


def _num(text) -> float | None:
    try:
        return float(str(text).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _won_to_text(won: float) -> str:
    """원 단위 → '6,512만 원' / '1억 2,340만 원'."""
    man = int(round(won / 10000))
    if man >= 10000:
        eok, rest = divmod(man, 10000)
        return f"{eok}억 {rest:,}만 원" if rest else f"{eok}억 원"
    return f"{man:,}만 원"


def _big_won(won: float) -> str:
    """매출처럼 큰 금액: '1조 2,345억 원' / '3,210억 원'."""
    eok = int(round(won / 1e8))
    if eok >= 10000:
        jo, rest = divmod(eok, 10000)
        return f"{jo}조 {rest:,}억 원" if rest else f"{jo}조 원"
    return f"{eok:,}억 원"


# ── 고용24 청년친화강소기업 ──────────────────────────────────
@cache_success(ttl=86400)
def smallgiants(region: str = SEOUL) -> list[dict] | None:
    """지역의 강소기업 전체 목록(API가 업종 검색을 지원하지 않아 한 번 받아 두고 걸러요)."""
    key = _sg_key()
    if not key:
        return None
    rows: list[dict] = []
    try:
        for page in range(1, 60):
            r = requests.get(SG_URL, params={"authKey": key, "callTp": "L", "returnType": "XML",
                                             "startPage": page, "display": 100, "region": region}, timeout=20)
            root = ET.fromstring(r.content)
            items = root.findall("smallGiant")
            if not items:
                break
            rows += [{c.tag: (c.text or "").strip() for c in s} for s in items]
            total = int(root.findtext("total") or 0)
            if len(rows) >= total:
                break
    except Exception:
        return rows or None
    return rows or None


def _industries(job: str) -> list[str]:
    for pat, codes in _INDUSTRY:
        if re.search(pat, job, re.I):
            return codes
    return ["J", "M", "C"]


def smallgiant_examples(job: str, n: int = 3) -> list[dict]:
    rows = smallgiants() or []
    codes = _industries(job)
    generic = {"사무원", "기획", "관리", "전문가", "종사자", "관리자", "담당자"}
    words = [w for w in re.split(r"[·\s/,()]+", job) if len(w) >= 2 and w not in generic]
    pool = [r for r in rows if r.get("superIndTpCd") in codes and (_num(r.get("alwaysWorkerCnt")) or 0) >= 10]

    def score(r: dict) -> tuple:
        text = f"{r.get('coMainProd', '')} {r.get('indTpNm', '')}"
        hit = sum(1 for w in words if w in text)
        return (hit, int(_num(r.get("alwaysWorkerCnt")) or 0))

    pool.sort(key=score, reverse=True)
    out, seen = [], set()
    for r in pool:
        k = norm(r.get("coNm", ""))
        if k and k not in seen:
            seen.add(k)
            out.append(r)
        if len(out) >= n:
            break
    return out


def _sg_line(r: dict) -> str:
    return (f"- {r.get('coNm')} · {r.get('regionNm')} · {r.get('indTpNm')} · 주요 제품·서비스: {(r.get('coMainProd') or '-')[:40]}"
            f" · 상시 근로자 {int(_num(r.get('alwaysWorkerCnt')) or 0):,}명 · {r.get('sgBrandNm')}({r.get('selYear')}) [{SG_SOURCE}]")


# ── 국민연금 가입 사업장 ─────────────────────────────────────
def _nps_get(op: str, **params) -> list[dict]:
    key = _nps_key()
    if not key:
        return []
    try:
        body = requests.get(NPS_URL + op, params={"serviceKey": key, "dataType": "json", "pageNo": 1,
                                                  "numOfRows": params.pop("rows", 20), **params}, timeout=8).json()
        items = (body.get("response", {}).get("body", {}).get("items") or {})
        items = items.get("item", []) if isinstance(items, dict) else []
        return items if isinstance(items, list) else [items]
    except Exception:
        return []


@cache_success(ttl=86400)
def nps_info(name: str, bizno6: str = "") -> dict | None:
    """회사 이름(+사업자번호 앞 6자리)으로 가장 최근 국민연금 가입 현황."""
    items = _nps_get("getBassInfoSearchV2", wkplNm=name, rows=30)
    target = norm(name)
    cands = [x for x in items if "/" not in (x.get("wkplNm") or "")]  # '회사/일용/공사현장' 같은 현장 사업장 제외
    if bizno6:
        cands = [x for x in cands if str(x.get("bzowrRgstNo", "")).startswith(bizno6)] or []
    exact = [x for x in cands if norm(x.get("wkplNm", "")) == target]
    cands = exact or ([] if bizno6 else [x for x in cands if norm(x.get("wkplNm", "")).startswith(target)])
    if not cands:
        return None
    best = sorted(cands, key=lambda x: str(x.get("dataCrtYm", "")), reverse=True)[0]
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(2) as ex:  # 상세·월별 현황을 동시에
        f1 = ex.submit(_nps_get, "getDetailInfoSearchV2", seq=best["seq"])
        f2 = ex.submit(_nps_get, "getPdAcctoSttusInfoSearchV2", seq=best["seq"])
        detail, period = (f1.result() or [{}])[0], (f2.result() or [{}])[0]
    count = detail.get("jnngpCnt")
    if not count:
        return None
    ym = str(best.get("dataCrtYm", ""))
    return {
        "name": best.get("wkplNm"), "ym": f"{ym[:4]}년 {int(ym[4:6])}월" if len(ym) == 6 else ym,
        "members": int(count), "industry": detail.get("vldtVlKrnNm"),
        "joined": period.get("nwAcqzrCnt"), "left": period.get("lssJnngpCnt"),
        "since": str(detail.get("adptDt", ""))[:4],
    }


def _nps_line(x: dict) -> str:
    flow = ""
    if x.get("joined") is not None and x.get("left") is not None:
        flow = f", 그달 입사 {x['joined']}명·퇴사 {x['left']}명"
    since = f", {x['since']}년부터 가입" if x.get("since") and x["since"] != "0001" else ""
    return f"- 국민연금({x['ym']} 기준): {x['name']} · {x.get('industry') or '업종 미상'} · 가입자(직원) {x['members']:,}명{flow}{since} [{NPS_SOURCE}]"


# ── DART ────────────────────────────────────────────────────
@cache_success(ttl=86400)
def dart_corps() -> list[tuple[str, str, str]] | None:
    """DART 회사 코드 목록 [(회사명, corp_code, stock_code)]. 공식 압축 파일을 하루 한 번 받아요."""
    key = _dart_key()
    if not key:
        return None
    try:
        r = requests.get(DART_URL + "corpCode.xml", params={"crtfc_key": key}, timeout=60)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            root = ET.fromstring(z.read(z.namelist()[0]))
    except Exception:
        return None
    out = []
    for c in root.iter("list"):
        out.append(((c.findtext("corp_name") or "").strip(), (c.findtext("corp_code") or "").strip(),
                    (c.findtext("stock_code") or "").strip()))
    return out or None


def _dart_index() -> tuple[dict[str, tuple], dict[str, tuple]]:
    """(상장사 이름 → 정보, 전체 이름 → 정보). 같은 이름이 여럿이면 상장사를 우선해요."""
    listed, every = {}, {}
    for name, code, stock in dart_corps() or []:
        k = norm(name)
        if not k:
            continue
        if stock:
            listed.setdefault(k, (name, code, stock))
        if k not in every or (stock and not every[k][2]):
            every[k] = (name, code, stock)
    return listed, every


def _dart_get(op: str, **params) -> dict:
    key = _dart_key()
    if not key:
        return {}
    try:
        return requests.get(DART_URL + op, params={"crtfc_key": key, **params}, timeout=15).json()
    except Exception:
        return {}


@cache_success(ttl=86400)
def dart_info(corp_code: str) -> dict | None:
    co = _dart_get("company.json", corp_code=corp_code)
    if co.get("status") != "000":
        return None
    info = {"name": co.get("corp_name"), "ceo": co.get("ceo_nm"), "est": co.get("est_dt", ""),
            "bizno6": (co.get("bizr_no") or "")[:6], "url": co.get("hm_url")}
    this_year = date.today().year
    for year in (this_year - 1, this_year - 2):
        emp = _dart_get("empSttus.json", corp_code=corp_code, bsns_year=str(year), reprt_code="11011")
        rows = emp.get("list") or []
        if emp.get("status") == "000" and rows:
            total = sum(_num(r.get("sm")) or 0 for r in rows)
            pay = sum(_num(r.get("fyer_salary_totamt")) or 0 for r in rows)
            tenure_w = [(_num(r.get("avrg_cnwk_sdytrn")), _num(r.get("sm")) or 0) for r in rows]
            tenure_w = [(t, w) for t, w in tenure_w if t is not None and w]
            info["emp_year"] = year
            info["employees"] = int(total) if total else None
            info["avg_pay"] = (pay / total) if total and pay else None
            info["tenure"] = (sum(t * w for t, w in tenure_w) / sum(w for _, w in tenure_w)) if tenure_w else None
            break
    for year in (this_year - 1, this_year - 2):
        fin = _dart_get("fnlttSinglAcnt.json", corp_code=corp_code, bsns_year=str(year), reprt_code="11011")
        rows = fin.get("list") or []
        if fin.get("status") == "000" and rows:
            pick = [r for r in rows if r.get("fs_div") == "CFS"] or rows
            acc = {r.get("account_nm"): _num(r.get("thstrm_amount")) for r in pick}
            info["fin_year"] = year
            info["sales"] = acc.get("매출액") or acc.get("수익(매출액)") or acc.get("영업수익")
            info["op"] = acc.get("영업이익") or acc.get("영업이익(손실)")
            break
    return info


def _dart_line(x: dict) -> str:
    parts = [f"- DART: {x['name']}"]
    if x.get("est") and len(x["est"]) == 8:
        parts.append(f"설립 {x['est'][:4]}년")
    if x.get("employees"):
        parts.append(f"직원 {x['employees']:,}명({x['emp_year']} 사업보고서)")
    if x.get("tenure"):
        parts.append(f"평균 근속 {x['tenure']:.1f}년")
    if x.get("avg_pay"):
        parts.append(f"1인 평균 급여 {_won_to_text(x['avg_pay'])}")
    if x.get("sales"):
        parts.append(f"매출 {_big_won(x['sales'])}({x['fin_year']}년)")
    if x.get("op") is not None and x.get("sales"):
        parts.append(f"영업이익 {_big_won(x['op'])}" if x["op"] >= 0 else f"영업손실 {_big_won(-x['op'])}")
    return " · ".join(parts) + f" [{DART_SOURCE}]"


# ── 목록 미리 받아 두기 ──────────────────────────────────────
_WARMED = False


def warm() -> None:
    """강소기업·DART 목록은 처음 받을 때 10~20초 걸려서, 앱이 뜰 때 뒤에서 미리 받아 둬요."""
    global _WARMED
    if _WARMED or not is_enabled():
        return
    _WARMED = True
    import threading

    def run():
        for fn in (smallgiants, dart_corps):
            try:
                fn()
            except Exception:
                pass

    threading.Thread(target=run, daemon=True).start()


# ── 질문에서 회사 찾기 ───────────────────────────────────────
def _tokens(question: str) -> list[str]:
    out = []
    for raw in re.findall(r"[가-힣A-Za-z0-9&]+", question):
        t = raw
        for p in _PARTICLES:
            if t.endswith(p) and len(t) - len(p) >= 2:
                t = t[: -len(p)]
                break
        out.append(t)
    return out


def find_companies(question: str, limit: int = 2) -> list[dict]:
    """질문에 나온 회사를 공공데이터에서 찾아요. [{'name', 'dart', 'nps', 'sg'}]"""
    toks = _tokens(question)
    warm()
    grams = toks + [a + b for a, b in zip(toks, toks[1:])]  # 'LG 전자'처럼 띄어 쓴 이름
    listed, every = _dart_index()
    sg_rows = {norm(r.get("coNm", "")): r for r in (smallgiants() or [])}
    talk = bool(_COMPANY_WORDS.search(question))
    found: list[dict] = []
    seen: set[str] = set()
    for g in sorted(set(grams), key=len, reverse=True):
        k = norm(g)
        if len(k) < 2 or k in seen or g in _STOP:
            continue
        hit = None
        if k in listed and (len(k) >= 3 or talk):  # 짧은 상장사 이름(예: 대상)은 회사 이야기일 때만
            hit = {"name": listed[k][0], "corp": listed[k][1]}
        elif talk and k in every:
            hit = {"name": every[k][0], "corp": every[k][1]}
        elif k in sg_rows:
            hit = {"name": sg_rows[k].get("coNm"), "corp": None}
        if hit:
            seen.add(k)
            found.append(hit)
        if len(found) >= limit:
            break
    # 목록에 없더라도 '○○ 회사 어때요'처럼 물으면 국민연금에서 한 번 찾아봐요(작은 회사). 추천 질문에서는 하지 않아요.
    if not found and talk and not _RECO.search(question):
        cands = [g for g in toks if g not in _STOP and len(norm(g)) >= 2 and not re.fullmatch(r"[0-9]+", g)
                 and not _VERBISH.search(g) and not _COMPANY_WORDS.search(g)][:2]
        for g in cands:
            info = nps_info(g, "") if _nps_key() else None
            if info:
                found.append({"name": g, "corp": None, "nps_done": info})
                break
        else:
            if cands:
                found.append({"name": cands[0], "corp": None, "nps_done": None})  # 못 찾았다고 알려 주려고 남겨요
    for f in found:
        f["dart"] = dart_info(f["corp"]) if f.get("corp") else None
        f["sg"] = sg_rows.get(norm(f["name"]))
        biz = (f["dart"] or {}).get("bizno6") or ((f["sg"] or {}).get("busiNo") or "")[:6]
        f["nps"] = f["nps_done"] if "nps_done" in f else nps_info(f["name"], biz)
    return [f for f in found if f["dart"] or f["nps"] or f["sg"]] + [
        {"name": f["name"], "missing": True} for f in found if not (f["dart"] or f["nps"] or f["sg"])
    ]


def evidence(question: str, job: str) -> tuple[str | None, list[str]]:
    """채팅 질문에 회사 이야기가 있으면 근거 문단과 출처를 돌려줘요. 없으면 (None, [])."""
    if not is_enabled():
        return None, []
    reco = bool(_RECO.search(question))
    lines: list[str] = []
    sources: list[str] = []
    try:
        named = find_companies(question)
    except Exception:
        named = []
    for f in named:
        if f.get("missing"):
            lines.append(f"- '{f['name']}': DART·국민연금·강소기업 공공데이터에서 찾지 못했어요(모른다고 솔직히 말하기)")
            continue
        lines.append(f"[{f['name']}]")
        if f.get("dart"):
            lines.append(_dart_line(f["dart"]))
            sources.append(DART_SOURCE)
        if f.get("nps"):
            lines.append(_nps_line(f["nps"]))
            sources.append(NPS_SOURCE)
        if f.get("sg"):
            lines.append(_sg_line(f["sg"]))
            sources.append(SG_SOURCE)
    if reco and not [f for f in named if not f.get("missing")]:
        try:
            ex = smallgiant_examples(job)
        except Exception:
            ex = []
        if ex:
            lines.append(f"[{job} 관련 업종의 청년친화강소기업 예시 · 서울]")
            lines += [_sg_line(r) for r in ex]
            sources.append(SG_SOURCE)
    if not lines:
        return None, []
    rule = ("[회사 정보 쓰는 법] 회사 소개는 아래 숫자만 그대로 쓰고 3~4문장으로 짧게 해요. 아래 줄을 그대로 붙여 넣지 말고 자연스러운 문장으로 풀어 써요. "
            "채용 중인지는 알 수 없다고 밝혀요. 아래 목록에 없는 회사 이름은 새로 꺼내지 않고, 궁금한 회사 이름을 물어보면 공공데이터로 알려 줄 수 있다고 안내해요. "
            "출처를 적을 때는 각 줄 끝 [ ] 안의 기관 이름(예: DART 전자공시(금융감독원), 국민연금 가입 사업장 내역(국민연금공단), "
            "고용24 청년친화강소기업(고용노동부))을 그대로 쓰고, 무엇을 가져왔는지는 '카카오뱅크 직원 수·평균 급여'처럼 짧게 적어요.")
    return "[회사 정보 · 공공데이터]\n" + rule + "\n" + "\n".join(lines), list(dict.fromkeys(sources))
