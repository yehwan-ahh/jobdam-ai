"""커리어 로드맵: 고른 직무·갈림길로 '지금 → 3년 뒤'를 길(도로) 위 이정표로 보여 줍니다."""

import html

import streamlit as st

from utils import profile, qnet, roadmap, training
from utils.demo_data import FUTURES
from utils.evidence import recommend_candidates
from utils.style import card

S = st.session_state
st.title("커리어 로드맵 🛣️", anchor=False)
st.caption("직무와 갈림길을 고르면 '지금의 나'에서 '3년 뒤의 나'까지 가는 길을 이정표로 그려 줘요. 자격·시험일정·교육과정은 공공데이터, 단계별 행동은 AI 제안이에요.")

# ── 입력 ─────────────────────────────────────────────────────
default_job = (S.get("selected_job") or {}).get("name")
options = list(dict.fromkeys(([default_job] if default_job else []) + recommend_candidates(S.get("my_major"))))
c1, c2, c3 = st.columns([1.4, 1.2, 1], gap="medium")
with c1:
    job = st.selectbox("목표 직무", options, index=0 if default_job else None, placeholder="직무를 고르거나 입력하세요",
                       accept_new_options=True, key="rm_job")
with c2:
    path = st.segmented_control("갈림길", list(FUTURES.keys()), default=S.get("future_choice") or "취업/이직", key="rm_path")
with c3:
    start = st.selectbox("지금 나는", roadmap.STARTS, index=2, key="rm_start")
me = profile.get()
st.caption(f":material/person_search: 내 프로필 반영: {profile.summary_line(me)}" if me else
           ":material/person_search: '내 프로필'을 채우면 내 강점·채울 능력에 맞춰 단계 목표가 달라져요.")

go = st.button("로드맵 그리기", type="primary", icon=":material/route:", disabled=not (job and path))
if go:
    with st.spinner("공공데이터를 모아 3년 길을 그리는 중…"):
        data = roadmap.gather(job, path)
        plan = roadmap.generate(data, start)
    S.roadmap = {"job": job, "path": path, "start": start, "data": data, "plan": plan}

rm = S.get("roadmap")
if not rm:
    st.stop()
data, plan = rm["data"], rm["plan"]


# ── 길 그림 (SVG) ────────────────────────────────────────────
def _wrap(text: str, width: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines[:2]


def road_svg(plan: dict, rm: dict) -> str:
    e = html.escape
    pts = [(270, 150), (510, 292), (750, 140), (990, 282)]
    start, end = (70, 300), (1140, 128)
    d = (f"M{start[0]},{start[1]} C170,300 170,{pts[0][1]} {pts[0][0]},{pts[0][1]} "
         f"S410,{pts[1][1]} {pts[1][0]},{pts[1][1]} S650,{pts[2][1]} {pts[2][0]},{pts[2][1]} "
         f"S890,{pts[3][1]} {pts[3][0]},{pts[3][1]} S1080,{end[1]} {end[0]},{end[1]}")
    out = [
        '<svg viewBox="0 0 1200 420" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block"'
        ' font-family="Noto Sans KR, Malgun Gothic, sans-serif">',
        '<rect x="0" y="0" width="1200" height="420" rx="22" fill="#F4F4F1"/>',
        # 지도 느낌의 점 무늬
        '<defs><pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">'
        '<circle cx="2" cy="2" r="1.2" fill="#DDDDD8"/></pattern></defs>',
        '<rect x="0" y="0" width="1200" height="420" rx="22" fill="url(#dots)"/>',
        f'<path d="{d}" fill="none" stroke="#D6D6D1" stroke-width="56" stroke-linecap="round"/>',
        f'<path d="{d}" fill="none" stroke="#2A2A2A" stroke-width="44" stroke-linecap="round"/>',
        f'<path d="{d}" fill="none" stroke="#FFFFFF" stroke-width="3" stroke-dasharray="16 14" stroke-linecap="round"/>',
        # 출발
        f'<circle cx="{start[0]}" cy="{start[1]}" r="20" fill="#FFFFFF" stroke="#111111" stroke-width="4"/>',
        f'<circle cx="{start[0]}" cy="{start[1]}" r="7" fill="#111111"/>',
        f'<text x="{start[0] - 10}" y="{start[1] + 52}" font-size="17" font-weight="800" fill="#111111">지금의 나</text>',
        f'<text x="{start[0] - 10}" y="{start[1] + 74}" font-size="13" fill="#6B6B6B">{e(rm["start"])}</text>',
    ]
    for i, ((x, y), s) in enumerate(zip(pts, plan["stages"])):
        up = y < 200
        ly = y - 62 if up else y + 54
        out += [
            f'<circle cx="{x}" cy="{y}" r="25" fill="#111111" stroke="#FFFFFF" stroke-width="4"/>',
            f'<text x="{x}" y="{y + 7}" text-anchor="middle" font-size="19" font-weight="800" fill="#FFFFFF">{i + 1}</text>',
            f'<text x="{x}" y="{ly}" text-anchor="middle" font-size="13" font-weight="700" fill="#6B6B6B">{e(s["period"])}</text>',
            f'<text x="{x}" y="{ly + 24}" text-anchor="middle" font-size="19" font-weight="800" fill="#111111">{e(s["title"])}</text>',
        ]
    # 도착(깃발)
    fx, fy = end
    out += [
        f'<line x1="{fx}" y1="{fy}" x2="{fx}" y2="{fy - 70}" stroke="#111111" stroke-width="4" stroke-linecap="round"/>',
        f'<path d="M{fx},{fy - 70} L{fx + 44},{fy - 58} L{fx},{fy - 46} Z" fill="#111111"/>',
        f'<text x="{fx + 30}" y="{fy + 50}" text-anchor="end" font-size="17" font-weight="800" fill="#111111">3년 뒤의 나</text>',
    ]
    for j, line in enumerate(_wrap(plan["checkpoint"], 22)):
        out.append(f'<text x="{fx + 30}" y="{fy + 74 + j * 20}" text-anchor="end" font-size="13" fill="#6B6B6B">{e(line)}</text>')
    out.append(f'<text x="40" y="44" font-size="22" font-weight="800" fill="#111111">{e(rm["job"])} · {e(rm["path"])}</text>')
    out.append(f'<text x="40" y="70" font-size="15" fill="#555555">{e(plan["headline"])}</text>')
    out.append("</svg>")
    return "".join(out)


svg = road_svg(plan, rm)
st.space("small")
st.html(svg)

# 이 길의 숫자(KOSIS)
stat = data.get("stat")
if stat is not None and not stat.error and stat.metrics:
    with st.container(horizontal=True):
        for label, value in stat.metrics:
            st.metric(label, value, border=True, width="content")
    st.caption(f":material/link: {stat.source}, KOSIS")

# ── 단계 카드 ────────────────────────────────────────────────
st.space("small")
cols = st.columns(len(plan["stages"]), gap="small")
for i, (col, s) in enumerate(zip(cols, plan["stages"])):
    with card(f"rm-stage-{i}", "white", parent=col):
        st.html(f'<div class="jd-opt-head"><span class="jd-opt-num">{i + 1}</span>'
                f'<span class="jd-opt-title" style="font-size:1.1rem">{html.escape(s["title"])}</span></div>')
        st.caption(s["period"])
        if s["goals"]:
            st.markdown("**목표**  \n" + "  \n".join(f"· {g}" for g in s["goals"]))
        if s["actions"]:
            st.markdown("**할 일**  \n" + "  \n".join(f"☐ {a}" for a in s["actions"]))
        for c in s["certs"]:
            rounds, ref = data["cert_rounds"].get(c, ([], False))
            st.markdown(f"**자격** · {c}")
            if rounds:
                r = rounds[0]
                st.caption(f"{'올해 일정 참고 · ' if ref else ''}{r['회차']}  \n필기 접수 {r['필기 접수']} · 필기 {r['필기 시험']} · 실기 {r['실기 시험']}")
            elif qnet.other_body(c):
                st.caption(f"시험은 {qnet.other_body(c)}에서 따로 시행해요. 일정은 그 기관에서 확인해 주세요.")
            elif qnet.kind_of(c) is None:
                st.caption("Q-Net 정기시험이 아니어서 주관 기관 일정을 확인해 주세요.")
        for title in s["courses"]:
            link = next((x["link"] for x in data["courses"] if x["title"] == title), "")
            st.markdown(f"**국비 교육** · [{title}]({link})" if link else f"**국비 교육** · {title}")

# ── 출처·내려받기 ─────────────────────────────────────────────
st.space("small")
srcs = []
if data["has_traits"]:
    srcs.append(f"고용24 직업정보 '{data['job_name']}'(중요 능력·관련 자격)")
if any(r for r, _ in data["cert_rounds"].values()):
    srcs.append(qnet.SOURCE)
if data["courses"]:
    srcs.append(training.SOURCE)
if stat is not None and not stat.error:
    srcs.append("KOSIS")
st.caption(
    ":material/link: 근거: " + (" · ".join(srcs) or "공공데이터 없음")
    + (" · 단계 이름·목표·할 일은 AI 제안이에요." if plan.get("ai") else " · AI 연결 전이라 데이터로 만든 기본 로드맵이에요.")
)
if any(ref for _, ref in data["cert_rounds"].values()):
    st.caption(":material/info: 내년 시험 일정이 아직 발표되지 않아, 올해 일정을 참고로 보여 줘요. 보통 해마다 비슷한 시기에 열려요.")


def export_html() -> str:
    e = html.escape
    parts = [f"<!doctype html><html lang='ko'><head><meta charset='utf-8'><title>잡담 커리어 로드맵 · {e(rm['job'])}</title>",
             "<style>body{font-family:'Noto Sans KR','Malgun Gothic',sans-serif;max-width:1100px;margin:32px auto;padding:0 16px;color:#111}"
             ".grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px;margin-top:18px}"
             ".c{border:1px solid #DDD;border-radius:16px;padding:16px}.p{color:#6B6B6B;font-size:13px}h3{margin:4px 0 8px}"
             "li{margin:3px 0}</style></head><body>", svg, "<div class='grid'>"]
    for i, s in enumerate(plan["stages"]):
        parts.append(f"<div class='c'><div class='p'>{i + 1} · {e(s['period'])}</div><h3>{e(s['title'])}</h3>")
        if s["goals"]:
            parts.append("<b>목표</b><ul>" + "".join(f"<li>{e(g)}</li>" for g in s["goals"]) + "</ul>")
        if s["actions"]:
            parts.append("<b>할 일</b><ul>" + "".join(f"<li>☐ {e(a)}</li>" for a in s["actions"]) + "</ul>")
        if s["certs"]:
            parts.append("<b>자격</b><ul>" + "".join(f"<li>{e(c)}</li>" for c in s["certs"]) + "</ul>")
        if s["courses"]:
            parts.append("<b>국비 교육</b><ul>" + "".join(f"<li>{e(c)}</li>" for c in s["courses"]) + "</ul>")
        parts.append("</div>")
    parts.append(f"</div><p class='p'>근거: {e(' · '.join(srcs))}. 단계별 행동은 AI 제안이며 참고용이에요. 잡담(Job談) · jobdam.streamlit.app</p></body></html>")
    return "".join(parts)


with st.container(horizontal=True):
    st.download_button("로드맵 내려받기 (HTML · 인쇄하면 PDF)", export_html(), file_name=f"잡담_로드맵_{rm['job']}.html",
                       mime="text/html", icon=":material/download:")
    if st.button("이 길의 '3년 뒤의 나'와 대화하기", icon=":material/forum:"):
        S.future_choice = rm["path"]
        st.switch_page("app_pages/future.py")
