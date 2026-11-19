"""AI 시대 새 직업: 공공 직업분류 밖의 신흥 직무 카드 + 융합 커리어 찾기."""

import streamlit as st

from utils import new_jobs
from utils.style import card

S = st.session_state
st.title("AI 시대 새 직업 🚀", anchor=False)
st.caption(
    "FDE·RAG 엔지니어처럼 공공 직업분류에 아직 없는 새 직업이에요. 설명은 AI로 정리한 뒤 다듬었고, "
    "실제 채용·보도 사례는 링크로 확인할 수 있어요. 연봉·전망 숫자는 가장 가까운 공공 직업의 고용24 자료로 보여 줘요."
)


def talk(job: dict) -> None:
    S.selected_job = {"name": job["name"], "why": job["one_line"], "basis": "AI 시대 새 직업 카드(잡담 큐레이션)"}
    S.just_chosen = True


def roadmap(job: dict) -> None:
    S.selected_job = {"name": job["name"], "why": job["one_line"], "basis": "AI 시대 새 직업 카드(잡담 큐레이션)"}


# ── 융합 커리어 찾기 ──────────────────────────────────────────
with card("nj-fusion", "white"):
    st.markdown("#### 융합 커리어 찾기")
    st.caption("내 전공·도메인과 가진 역량을 고르면, 둘을 함께 살릴 수 있는 새 직업을 찾아 줘요. 예: 반도체 + Python → 반도체 데이터 엔지니어, FDE")
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        doms = st.multiselect("내 전공·도메인", new_jobs.all_domains(), key="nj_domains", placeholder="예: 반도체, 제조")
    with c2:
        skills = st.multiselect("가진 역량·관심 기술", new_jobs.all_skills(), key="nj_skills", accept_new_options=True,
                                placeholder="예: Python, 통계")
    if doms or skills:
        found = new_jobs.match(doms, skills)[:4]
        if found:
            st.markdown("**나와 잘 이어지는 새 직업** · " + " · ".join(f"{j['name']}" for j, _ in found))
        else:
            st.caption("겹치는 직업이 없어요. 도메인이나 기술을 바꿔 보세요.")

# ── 카드 목록 ────────────────────────────────────────────────
st.space("small")
cat = st.pills("분야", ["전체"] + new_jobs.categories(), default="전체", key="nj_cat")
items = [j for j in new_jobs.jobs() if cat in (None, "전체") or j["category"] == cat]
if doms or skills:
    order = {j["name"]: sc for j, sc in new_jobs.match(doms, skills)}
    items.sort(key=lambda j: -order.get(j["name"], 0))
st.caption(f"{len(items)}개 직업")

cols = st.columns(3, gap="medium")
for i, job in enumerate(items):
    with card(f"nj-{i}", "white", parent=cols[i % 3]):
        st.caption(f"{job['category']} · {job['en']}")
        st.markdown(f"#### {job['name']}")
        st.markdown(job["one_line"])
        st.markdown(" ".join(f"`{s}`" for s in job["skills"]))
        with st.expander("하는 일 · 준비 방법 · 출처"):
            st.markdown("**하는 일**  \n" + "  \n".join(f"· {d}" for d in job["duties"]))
            st.markdown("**준비 방법**  \n" + "  \n".join(f"· {p}" for p in job["prepare"]))
            if job.get("sources"):
                st.markdown("**실제 채용·보도 사례**  \n" + "  \n".join(f"· [{s['title']}]({s['url']})" for s in job["sources"]))
            else:
                st.caption("국내 채용 사례는 아직 확인하지 못한 신흥 직무예요.")
            st.caption(f":material/link: 숫자는 가장 가까운 공공 직업 '{job['related']}'(고용24) 기준")
        with st.container(horizontal=True):
            if st.button("선배와 대화", key=f"nj-talk-{i}", icon=":material/forum:", type="primary", on_click=talk, args=(job,)):
                st.switch_page("app_pages/panel.py")
            if st.button("로드맵", key=f"nj-road-{i}", icon=":material/route:", on_click=roadmap, args=(job,)):
                st.switch_page("app_pages/roadmap.py")

st.space("small")
st.caption(
    ":material/info: 직업 목록·한 줄 설명·핵심 기술은 팀이 고르고, 하는 일·준비 방법은 생성형 AI로 초안을 쓴 뒤 다듬었어요. "
    "공공 통계가 없는 직업이라 숫자는 만들지 않고, 출처 링크는 실제로 확인한 것만 달았어요."
)
