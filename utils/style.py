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

/* 간이검사 결과지: 큰 흰 박스 + 진한 테두리 */
[class*="st-key-pf-report"], [class*="st-key-future-synth"] {{
    background: #FFFFFF; border: 2px solid #111111; border-radius: 24px; padding: 1.8rem 1.9rem;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05), 0 18px 48px rgba(0,0,0,0.08);
}}
[class*="st-key-pf-report"] [class*="st-key-card-white-"], [class*="st-key-future-synth"] [class*="st-key-card-white-"] {{ border-color: #E5E5E5; box-shadow: none; background: #FBFBF9; }}
.jd-report-tag {{ display: inline-block; background: #111111; color: #FFFFFF; font-weight: 700; font-size: 0.9rem;
    padding: 0.35rem 0.8rem; border-radius: 999px; }}
[class*="st-key-pf-next"] {{ background: #F4F4F1; border-radius: 16px; padding: 0.9rem 1.1rem; }}

/* 직무 패널: '3년 뒤의 나와 채팅하기' 강조 띠 */
.st-key-cta-future {{
    background: #111111; border-radius: 20px; padding: 1.2rem 1.4rem;
    box-shadow: 0 10px 28px rgba(0,0,0,0.18);
}}
.st-key-cta-future p, .st-key-cta-future h4 {{ color: #FFFFFF !important; }}
.st-key-cta-future [data-testid="stCaptionContainer"] p {{ color: #CFCFCB !important; }}
.st-key-cta-future button {{ background: #FFFFFF !important; border-color: #FFFFFF !important; min-height: 3rem; }}
.st-key-cta-future button p {{ color: #111111 !important; font-weight: 800; font-size: 1.02rem; }}

/* 메인 로고: 둥근 모서리 */
[class*="st-key-card-white-intro-hero"] img {{ border-radius: 16px; }}

/* 직무 간이검사: 검사지처럼 문항은 크게, 다섯 칸은 모두 또렷하게 */
[class*="st-key-pfq-row-"] {{ padding: 0.85rem 0 0.95rem; border-bottom: 1px solid #EDEDEA; }}
.jd-q {{ font-size: 1.12rem; font-weight: 700; color: #111111; line-height: 1.5; display: flex; gap: 0.6rem; align-items: baseline; }}
.jd-q-num {{ flex: none; width: 1.7rem; height: 1.7rem; border-radius: 999px; background: #111111; color: #FFFFFF;
    font-size: 0.85rem; display: inline-flex; align-items: center; justify-content: center; }}
[class*="st-key-pfq-row-"] [data-testid="stButtonGroup"] button {{
    min-height: 2.8rem; font-size: 0.98rem; font-weight: 600; color: #333333; background: #FFFFFF; border-color: #CFCFCB;
}}
[class*="st-key-pfq-row-"] [data-testid="stButtonGroup"] button p {{ font-size: 0.98rem; font-weight: 600; }}
[class*="st-key-pfq-row-"] [data-testid="stButtonGroup"] button[aria-checked="true"],
[class*="st-key-pfq-row-"] [data-testid="stButtonGroup"] button[aria-pressed="true"] {{
    background: #111111 !important; color: #FFFFFF !important; border-color: #111111 !important;
}}
[class*="st-key-pfq-row-"] [data-testid="stButtonGroup"] button[aria-checked="true"] p,
[class*="st-key-pfq-row-"] [data-testid="stButtonGroup"] button[aria-pressed="true"] p {{ color: #FFFFFF !important; }}
[class*="st-key-pfq-row-"] [data-testid="stButtonGroup"] button:hover {{ border-color: #111111; }}
[data-testid="stBaseButton-segmented_controlActive"] {{ background: #111111 !important; color: #FFFFFF !important; border-color: #111111 !important; }}
[data-testid="stBaseButton-segmented_controlActive"] p {{ color: #FFFFFF !important; }}

/* 하단 채팅 입력창: 흰 바탕 + 검정 테두리로 또렷하게 */
[data-testid="stChatInput"] {{
    background: #FFFFFF !important;
    border: 1.5px solid #111111 !important;
    border-radius: 18px !important;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.10);
}}
[data-testid="stChatInput"] textarea {{ color: #111111 !important; font-size: 1rem; background: #FFFFFF !important; }}
[data-testid="stChatInput"] > div, [data-testid="stChatInput"] div[data-baseweb] {{ background: #FFFFFF !important; }}
[data-testid="stChatInput"] textarea::placeholder {{ color: #555555 !important; opacity: 1; }}
[data-testid="stChatInputSubmitButton"] {{ background: #111111 !important; color: #FFFFFF !important; border-radius: 999px !important; }}
[data-testid="stChatInputSubmitButton"] svg {{ fill: #FFFFFF !important; color: #FFFFFF !important; }}
[data-testid="stChatInput"]:focus-within {{ border-color: #000000 !important; box-shadow: 0 0 0 3px rgba(17,17,17,0.12), 0 6px 24px rgba(0,0,0,0.10); }}
[data-testid="stChatInput"] textarea {{ min-height: 3rem; }}
[data-testid="stBottom"] > div {{ background: linear-gradient(to top, #FFFFFF 70%, rgba(255,255,255,0)); border-top: 1px solid #E5E5E5; }}
@keyframes jdPulse {{
    0%, 100% {{ box-shadow: 0 0 0 0 rgba(17, 17, 17, 0.35), 0 6px 24px rgba(0, 0, 0, 0.10); }}
    50% {{ box-shadow: 0 0 0 8px rgba(17, 17, 17, 0.0), 0 6px 24px rgba(0, 0, 0, 0.10); }}
}}

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


_TOP_JS = """<script>
(() => {
  let stop = false;
  let self = false;
  const docs = [document];
  try { if (window.parent && window.parent.document) docs.push(window.parent.document); } catch (e) {}
  for (const d of docs) {
    ["wheel", "touchstart", "keydown"].forEach((ev) => d.addEventListener(ev, () => { if (!self) stop = true; }, { passive: true }));
  }
  const go = () => {
    if (stop) return;
    for (const d of docs) {
      const el = d.querySelector('[data-testid="stAppScrollToBottomContainer"]');
      if (el) {
        // 위로 굴린 것처럼 알려 '맨 아래 고정'을 풀고(화면 크기가 바뀌어도 다시 내려가지 않게) 맨 위로
        self = true;
        el.dispatchEvent(new WheelEvent("wheel", { deltaY: -400, bubbles: true }));
        self = false;
        el.scrollTop = 0;
      }
    }
    window.__jdTop = (window.__jdTop || 0) + 1;
  };
  [100, 400, 900, 1500, 2300, 3500].forEach((t) => setTimeout(go, t));
})();
</script>"""


def scroll_to_top() -> None:
    """채팅 입력창이 있는 페이지는 Streamlit이 맨 아래로 붙여서 엽니다.
    처음 들어왔을 때(대화 전) 위쪽의 선택 화면부터 보이도록 맨 위로 올립니다."""
    st.html(_TOP_JS, unsafe_allow_javascript=True)
