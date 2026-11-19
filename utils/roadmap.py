"""커리어 로드맵: 공공데이터(역량·자격·시험일정·훈련과정·KOSIS)를 모으고 AI가 4단계 길로 엮습니다.

AI가 없거나 실패하면 같은 데이터로 기본 로드맵을 만들어 화면이 비지 않게 합니다.
"""

from utils import compare, kosis, llm, new_jobs, profile, qnet, training

STAGES = ["지금 ~ 3개월", "3 ~ 6개월", "6개월 ~ 1년", "1 ~ 3년"]
STARTS = ["대학교 1~2학년", "대학교 3학년", "대학교 4학년·졸업 예정", "졸업 후 준비 중", "사회초년생(1~2년 차)"]
PATH_HINT = {
    "취업/이직": "인턴·직무 경험, 포트폴리오, 자격, 지원과 면접",
    "대학원 진학": "관심 연구 분야 정하기, 연구실 컨택, 학부 연구생·논문 읽기, 입시 준비",
    "창업": "문제 검증, 최소 제품(MVP), 정부 창업지원사업, 첫 고객 확보",
}


def gather(job: str, path: str) -> dict:
    """로드맵 재료(실제 데이터)."""
    t = profile.job_traits(job)
    p = profile.get()
    abilities = [n for n, _ in (t["abilities"] if t else [])][:5]
    gaps = profile.fit(p, t)["gaps"] if (p and t) else abilities[:3]
    certs = (t["certs"] if t else [])[:4]
    cert_rounds = {c: qnet.next_rounds(c) for c in certs}
    card = new_jobs.get(job)
    course_kw = card["keywords"][0] if card else job
    courses = (training.courses(course_kw, limit=3) if training.is_enabled() else None) or []
    stat = compare.stats(path) if kosis.is_enabled() else None
    return {
        "job": job, "path": path, "job_name": t["name"] if t else job,
        "abilities": abilities, "gaps": gaps, "certs": certs, "cert_rounds": cert_rounds,
        "courses": courses, "stat": stat, "has_traits": bool(t), "card": card,
    }


def evidence_text(d: dict) -> str:
    lines = [new_jobs.evidence(d["job"]) or ""] if d.get("card") else []
    lines.append(f"[고용24 · '{d['job_name']}' 직업정보]")
    if d["abilities"]:
        lines.append("- 중요한 능력(점수 높은 순): " + ", ".join(d["abilities"]))
    if d["gaps"]:
        lines.append("- 이 사용자가 채우면 좋은 능력: " + ", ".join(d["gaps"]))
    lines.append("<자격>" + (", ".join(d["certs"]) or "(없음)") + "</자격>")
    for c, (rounds, ref) in d["cert_rounds"].items():
        if rounds:
            r = rounds[0]
            lines.append(f"- {c} 시험({'올해 일정 참고' if ref else '다가오는 회차'}): {r['회차']} 필기 {r['필기 시험']}, 실기 {r['실기 시험']}")
    lines.append("<훈련과정>" + (" / ".join(f"{c['title']}({c['org']})" for c in d["courses"]) or "(없음)") + "</훈련과정>")
    if d["stat"] is not None and d["stat"].evidence:
        lines.append(d["stat"].evidence)
    return "\n".join(lines)


def baseline(d: dict) -> dict:
    """AI 없이 데이터만으로 만든 기본 로드맵."""
    gaps = d["gaps"] or ["직무 기초 역량"]
    certs = d["certs"]
    courses = [c["title"] for c in d["courses"]]
    hint = PATH_HINT.get(d["path"], "")
    return {
        "headline": f"{d['path']} 길로 '{d['job']}'에 닿기",
        "stages": [
            {"period": STAGES[0], "title": "방향 잡기", "goals": [f"'{d['job']}'이 하는 일 정확히 알기", f"{gaps[0]} 기초 다지기"],
             "actions": ["직무 선배에게 하루 일과·준비 방법 묻기", "관련 채용공고 3개 저장하고 공통 요구 역량 표시하기"], "certs": [], "courses": courses[:1]},
            {"period": STAGES[1], "title": "역량 쌓기", "goals": [f"{', '.join(gaps[:2])} 키우기"],
             "actions": ["작은 프로젝트 하나 완성하기", "스터디·동아리로 꾸준히 연습하기"], "certs": certs[:1], "courses": courses[1:2]},
            {"period": STAGES[2], "title": "증명하기", "goals": ["경험을 결과물로 남기기", "자격·포트폴리오 정리"],
             "actions": [f"{hint.split(',')[0] if hint else '실전 경험'} 시작하기", "결과물을 포트폴리오로 정리하기"], "certs": certs[1:2], "courses": courses[2:3]},
            {"period": STAGES[3], "title": "자리 잡기", "goals": [f"{d['path']} 길에서 첫 성과 내기"],
             "actions": ["3년 뒤의 나에게 물어보며 방향 점검하기", "다음 단계 목표 다시 세우기"], "certs": certs[2:3], "courses": []},
        ],
        "checkpoint": f"3년 뒤, '{d['job']}' 일을 하며 다음 길을 스스로 고를 수 있는 나",
        "ai": False,
    }


DEFAULT_TITLES = ["방향 잡기", "역량 쌓기", "증명하기", "자리 잡기"]


def _title(raw, i: int) -> str:
    """AI가 단계 이름 대신 기간('지금~3개월')을 넣으면 기본 이름으로 바꿉니다."""
    t = str(raw or "").strip()
    if not t or any(k in t for k in ("개월", "년", "지금")) or len(t) > 12:
        return DEFAULT_TITLES[min(i, 3)]
    return t


def generate(d: dict, start: str) -> dict:
    """AI 로드맵. 실패하면 기본 로드맵."""
    from utils.prompts import roadmap_system

    if not llm.is_enabled():
        return baseline(d)
    system = roadmap_system(d["job"], d["path"], start, PATH_HINT.get(d["path"], ""), evidence_text(d), profile.prompt_block(d["job"]))
    data, _ = llm.generate_json(system, [{"role": "user", "content": f"{start}인 내가 '{d['path']}' 길로 '{d['job']}'에 닿는 3년 로드맵을 그려 줘."}])
    stages = (data or {}).get("stages") if isinstance(data, dict) else None
    if not isinstance(stages, list) or len(stages) < 3:
        return baseline(d)
    allowed_certs, allowed_courses = set(d["certs"]), {c["title"] for c in d["courses"]}
    clean = []
    for i, s in enumerate(stages[:4]):
        if not isinstance(s, dict):
            continue
        clean.append({
            "period": STAGES[min(i, 3)],
            "title": _title(s.get("title"), i),
            "goals": [str(x) for x in (s.get("goals") or [])][:3],
            "actions": [str(x) for x in (s.get("actions") or [])][:3],
            # 자격·과정은 실제 데이터에 있는 것만 남깁니다(지어낸 이름 제거)
            "certs": [c for c in (s.get("certs") or []) if c in allowed_certs][:2],
            "courses": [c for c in (s.get("courses") or []) if c in allowed_courses][:1],
        })
    if len(clean) < 3:
        return baseline(d)
    seen: set[str] = set()  # 같은 자격은 처음 나온 단계에만
    for s in clean:
        s["certs"] = [c for c in s["certs"] if not (c in seen or seen.add(c))]
    # AI가 과정명을 바꿔 써서 걸러졌다면, 실제 훈련과정을 앞 단계부터 하나씩 붙입니다.
    if not any(s["courses"] for s in clean):
        for s, c in zip(clean, d["courses"]):
            s["courses"] = [c["title"]]
    return {
        "headline": str(data.get("headline", ""))[:60] or baseline(d)["headline"],
        "stages": clean,
        "checkpoint": str(data.get("checkpoint", ""))[:80] or baseline(d)["checkpoint"],
        "ai": True,
    }
