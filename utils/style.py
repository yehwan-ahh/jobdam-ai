"""파스텔 카드 스타일.

레퍼런스 대시보드처럼 둥글고 그림자가 은은한 카드를 만들기 위해,
key가 `card-<색>-...`, `tile-<색>-...`인 컨테이너에만 CSS를 적용합니다.
"""

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

# 네이비·틸 팔레트의 파스텔 톤 + 따뜻한 보조 톤
CARD_COLORS = {
    "white": "#FFFFFF",
    "sky": "#E6EEF8",    # 네이비 파스텔
    "mint": "#E2F3EF",   # 틸 파스텔
    "peach": "#FCEDE3",  # 따뜻한 보조
    "cream": "#FFF5DC",  # 따뜻한 보조
}
TILE_COLORS = {
    "navy": "#1E3A6E",
    "teal": "#0E8C83",
    "peach": "#F2B8A0",
    "cream": "#F5CF6B",
    "white": "#FFFFFF",
}

_CARD_CSS = "\n".join(
    f"""[class*="st-key-card-{name}-"] {{
    background: {color};
    border-radius: 22px;
    padding: 1.4rem 1.5rem;
    box-shadow: 0 8px 24px rgba(30, 58, 110, 0.07);
}}"""
    for name, color in CARD_COLORS.items()
)
_CSS = f"""
{_CARD_CSS}
.jd-tile {{
    width: 3.2rem; height: 3.2rem; border-radius: 16px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.55rem; line-height: 1;
    box-shadow: 0 4px 12px rgba(30, 58, 110, 0.12);
}}
.jd-big {{ font-size: 2.4rem; font-weight: 700; color: #1E3A6E; line-height: 1.1; margin: 0.2rem 0 0; }}
.jd-hero-emoji {{ font-size: 6rem; line-height: 1; text-align: center; padding-top: 0.5rem; }}
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
