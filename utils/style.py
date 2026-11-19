"""모노톤(흰색·회색·검정) 카드 스타일.

레퍼런스 대시보드처럼 둥글고 그림자가 은은한 카드를 만들기 위해,
key가 `card-<색>-...`, `tile-<색>-...`인 컨테이너에만 CSS를 적용합니다.
"""

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

# 흰색·회색·검정 모노톤. 색 이름(sky/mint/…)은 호출부 호환을 위해 유지하고 값만 회색 단계로 바꿉니다.
CARD_COLORS = {
    "white": "#FFFFFF",
    "sky": "#FFFFFF",
    "mint": "#FBFBF9",
    "peach": "#F4F4F1",
    "cream": "#EDEDEA",
}
TILE_COLORS = {
    "navy": "#111111",
    "teal": "#3A3A3A",
    "peach": "#8C8C8C",
    "cream": "#D4D4D4",
    "white": "#FFFFFF",
}

_CARD_CSS = "\n".join(
    f"""[class*="st-key-card-{name}-"] {{
    background: {color};
    border: 1px solid #E5E5E5;
    border-radius: 20px;
    padding: 1.5rem 1.6rem;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03), 0 8px 24px rgba(0, 0, 0, 0.04);
}}"""
    for name, color in CARD_COLORS.items()
)
_CSS = f"""
{_CARD_CSS}
.jd-tile {{
    width: 3.2rem; height: 3.2rem; border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.5rem; line-height: 1;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.10);
}}
.jd-big {{ font-size: 2.6rem; font-weight: 800; color: #111111; line-height: 1.05; letter-spacing: -0.02em; margin: 0.2rem 0 0; }}
.jd-hero-emoji {{ font-size: 6rem; line-height: 1; text-align: center; padding-top: 0.5rem; }}
h1, h2, h3 {{ letter-spacing: -0.02em; }}

/* 직무 고르기 옵션 카드: 진한 테두리 + 번호 배지 */
[class*="st-key-card-white-opt-"] {{
    border: 1.5px solid #111111;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04), 0 12px 32px rgba(0, 0, 0, 0.06);
}}
.jd-opt-head {{ display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.1rem; }}
.jd-opt-num {{
    width: 2rem; height: 2rem; border-radius: 999px; background: #111111; color: #FFFFFF;
    display: inline-flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1rem;
}}
.jd-opt-title {{ font-size: 1.35rem; font-weight: 800; color: #111111; letter-spacing: -0.02em; }}
/* 선택된 pill(직업)을 검정 배경·흰 글씨로 */
[data-testid="stBaseButton-pillsActive"] {{ background: #111111 !important; color: #FFFFFF !important; border-color: #111111 !important; }}
[data-testid="stBaseButton-pillsActive"] p {{ color: #FFFFFF !important; }}

/* 채팅 말풍선: 흰색 카드 박스로 글씨를 또렷하게 */
[data-testid="stChatMessage"] {{
    background: #FFFFFF;
    border: 1px solid #E5E5E5;
    border-radius: 18px;
    padding: 1.1rem 1.3rem;
    margin-bottom: 0.75rem;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03), 0 6px 18px rgba(0, 0, 0, 0.04);
}}
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li {{ color: #1A1A1A; line-height: 1.7; }}
[data-testid="stChatMessage"] [data-testid="stCaptionContainer"] p {{ color: #6B6B6B; line-height: 1.5; }}
"""


def apply_style() -> None:
    st.html(f"<style>{_CSS}</style>")


def card(key: str, color: str = "white", *, parent: DeltaGenerator | None = None) -> DeltaGenerator:
    """파스텔 카드 컨테이너. key는 페이지 안에서 고유해야 합니다."""
    target = parent if parent is not None else st
    return target.container(key=f"card-{color}-{key}", height="stretch")


def icon_tile(emoji: str, key: str, tone: str = "navy") -> None:
    """레퍼런스의 둥근 아이콘 타일. key는 호출부 호환을 위해 남겨 둡니다."""
    del key
    color = TILE_COLORS.get(tone, TILE_COLORS["navy"])
    st.html(f'<div class="jd-tile" style="background:{color}">{emoji}</div>', width="content")


def big_number(text: str) -> None:
    st.html(f'<div class="jd-big">{text}</div>')


def hero_emoji(emoji: str) -> None:
    st.html(f'<div class="jd-hero-emoji">{emoji}</div>')
