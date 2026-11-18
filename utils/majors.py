"""학과 → 상위 진출 직업 (한국고용정보원 상위진출직업, 2022-04-06).

data/major_top_jobs.csv: 계열정보, 학과명, 직업분류명 (원본 CP949 → UTF-8 변환만, 내용 변경 없음)
"""

from pathlib import Path

import pandas as pd
import streamlit as st

SOURCE = "한국고용정보원 상위진출직업(2022)"
CSV = Path(__file__).resolve().parent.parent / "data" / "major_top_jobs.csv"


@st.cache_data(show_spinner=False)
def load() -> pd.DataFrame:
    df = pd.read_csv(CSV, encoding="utf-8")
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    return df


def fields() -> list[str]:
    return sorted(load()["계열정보"].unique().tolist())


def majors(field: str | None = None) -> list[str]:
    df = load()
    if field:
        df = df[df["계열정보"] == field]
    return sorted(df["학과명"].unique().tolist())


def top_jobs(major: str) -> list[str]:
    df = load()
    return df.loc[df["학과명"] == major, "직업분류명"].tolist()


def evidence(major: str | None) -> str | None:
    """AI 근거자료용 한 줄."""
    if not major:
        return None
    jobs = top_jobs(major)
    if not jobs:
        return None
    return f"[{SOURCE}] 사용자의 학과 '{major}' 졸업자가 많이 진출하는 직업: " + ", ".join(jobs)


def render_picker(key_prefix: str) -> str | None:
    """계열 → 학과를 고르면 상위 진출 직업을 보여 주고, 고른 학과를 돌려줍니다. 고르지 않으면 None."""
    with st.expander("내 학과 졸업자는 어디로 갈까?", icon=":material/school:"):
        c1, c2 = st.columns(2)
        field = c1.selectbox("계열", fields(), index=None, placeholder="계열 선택", key=f"{key_prefix}_major_group")
        major = c2.selectbox(
            "학과",
            majors(field),
            index=None,
            placeholder="학과 선택 (검색 가능)",
            key=f"{key_prefix}_major_name",
        )
        if not major:
            st.caption("학과를 고르면 그 학과 졸업자가 많이 진출하는 직업을 보여 주고, AI 답변에도 참고해요.")
            return None
        with st.container(horizontal=True):
            for job in top_jobs(major):
                st.badge(job, color="blue")
        st.caption(f":material/link: 출처: {SOURCE} · 학과 이름은 개인정보가 아니며 저장하지 않아요.")
        return major
