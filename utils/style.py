"""잡담 디자인: 어두운 별빛 배경 + 라임 포인트 (UX/UI 디자인 시안 반영).

key가 `card-<색>-...`인 컨테이너는 어두운 패널 카드로, CTA 띠(`cta-*`)는 라임 버튼으로 보여 줍니다.
색 이름(white/sky/mint/…)은 호출부 호환을 위해 그대로 두고 값만 어두운 단계로 바꿉니다.
"""

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

INK, MUTED, LIME, LIME_INK = "#F5F3EA", "#B1AFA3", "#D9F477", "#171717"
PANEL, PANEL2, RULE, RULE2 = "#121310", "#151612", "#2F3029", "#45473B"

CARD_COLORS = {
    "white": PANEL,
    "sky": PANEL,
    "mint": "#141611",
    "peach": "#16150F",
    "cream": PANEL2,
}
TILE_COLORS = {
    "navy": LIME,
    "teal": "#5A5C4E",
    "peach": "#EFCE97",
    "cream": "#2F3029",
    "white": PANEL2,
}

_CARD_CSS = "\n".join(
    f"""[class*="st-key-card-{name}-"] {{
    background: {color};
    border: 1px solid {RULE};
    border-radius: 16px;
    padding: 1.35rem 1.45rem;
}}"""
    for name, color in CARD_COLORS.items()
)
_CTA = "\n".join(
    f""".st-key-{k} {{ background: linear-gradient(120deg, #151612, #191C12); border: 1px solid #3B4226; border-left: 4px solid {LIME};
    border-radius: 16px; padding: 1.15rem 1.35rem; }}
.st-key-{k} h4 {{ color: {INK} !important; }}
.st-key-{k} [data-testid="stCaptionContainer"] p {{ color: {MUTED} !important; }}
.st-key-{k} button {{ background: {LIME} !important; border-color: {LIME} !important; min-height: 2.9rem; padding: 0 1.3rem; box-shadow: 0 2px 10px rgba(217,244,119,0.18); }}
.st-key-{k} button p, .st-key-{k} button span {{ color: {LIME_INK} !important; font-weight: 760; font-size: 1rem; }}"""
    for k in ("cta-future", "cta-start", "cta-roadmap", "cta-rmgate")
)
_CSS = f"""
@import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css");
html, body, .stApp, button, input, textarea, p, li, label, h1, h2, h3, h4, h5 {{ font-family: "Pretendard", "Apple SD Gothic Neo", "Malgun Gothic", system-ui, sans-serif !important; }}
p, li, label {{ word-break: keep-all; overflow-wrap: anywhere; }}

/* 별빛 배경 */
.stApp {{
    background:
      radial-gradient(1px 1px at 12% 18%, rgba(255,255,255,.55) 50%, transparent 51%),
      radial-gradient(1px 1px at 72% 12%, rgba(255,255,255,.45) 50%, transparent 51%),
      radial-gradient(1.4px 1.4px at 38% 64%, rgba(255,255,255,.35) 50%, transparent 51%),
      radial-gradient(1px 1px at 88% 46%, rgba(255,255,255,.4) 50%, transparent 51%),
      radial-gradient(1px 1px at 22% 86%, rgba(255,255,255,.3) 50%, transparent 51%),
      radial-gradient(1.2px 1.2px at 56% 30%, rgba(217,244,119,.45) 50%, transparent 51%),
      radial-gradient(1px 1px at 94% 82%, rgba(255,255,255,.35) 50%, transparent 51%),
      radial-gradient(1px 1px at 6% 52%, rgba(255,255,255,.3) 50%, transparent 51%),
      radial-gradient(ellipse at 82% -12%, #1b1a2a 0%, transparent 48%),
      #080808;
    background-size: 420px 420px, 360px 360px, 520px 520px, 300px 300px, 460px 460px, 640px 640px, 380px 380px, 500px 500px, 100% 100%, auto;
    background-attachment: fixed;
}}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stSidebarCollapseButton"] {{ display: none !important; }}
.block-container {{ max-width: 1120px; }}
h1 {{ letter-spacing: -0.045em; }}
h2, h3, h4 {{ letter-spacing: -0.035em; }}
[data-testid="stCaptionContainer"] p {{ color: {MUTED}; }}

/* 위쪽 4단계 진행 메뉴 */
.st-key-topbar {{ border-bottom: 1px solid #2D2E27; padding: 0.1rem 0 0.5rem; margin-bottom: 0.4rem; gap: 0.5rem; }}
.st-key-topbar [data-testid="stPageLink"] a {{ padding: 0.25rem 0.35rem; border-radius: 6px; background: transparent !important; }}
.st-key-topbar [data-testid="stPageLink"] a p, .st-key-topbar [data-testid="stPageLink"] a span {{ font-size: 0.86rem; color: {MUTED} !important; font-weight: 560; white-space: nowrap; }}
.st-key-topbar [data-testid="stPageLink"] a:hover p {{ color: {INK} !important; }}
.st-key-nav-brand [data-testid="stPageLink"] a p {{ color: #F6F3EA !important; font-weight: 850 !important; font-size: 1rem !important; letter-spacing: -0.06em; }}
[class*="st-key-navstep-"] [data-testid="stPageLink"] a p::before {{
    content: ""; display: inline-block; width: 7px; height: 7px; margin-right: 7px; vertical-align: 1px;
    border: 1px solid #838477; border-radius: 50%;
}}
[class*="st-key-navstep-"][class*="-done"] [data-testid="stPageLink"] a p::before {{ background: {LIME}; border-color: {LIME}; }}
[class*="st-key-navstep-"][class*="-now"] [data-testid="stPageLink"] a p {{ color: #F6F3EA !important; font-weight: 760 !important; }}
[class*="st-key-navstep-"][class*="-now"] [data-testid="stPageLink"] a p::before {{ border-color: {LIME}; box-shadow: 0 0 6px #d9f47788; }}
.st-key-nav-steps {{ gap: 0.15rem; }}
.jd-nav-rule {{ width: clamp(8px, 1.6vw, 22px); height: 1px; background: #45473E; }}
.st-key-nav-steps [data-testid="stHtml"] {{ display: flex; align-items: center; }}
.st-key-topbar [data-testid="stPageLink"] [data-testid="stIconMaterial"] {{ display: none; }}
[data-testid^="stBaseButton-primary"]:disabled {{ opacity: .45; filter: grayscale(.3); }}
.st-key-nav-more button {{ background: transparent !important; border-color: {RULE2} !important; min-height: 2.1rem; }}
@media (max-width: 640px) {{
    .st-key-topbar {{ flex-wrap: wrap !important; row-gap: 0.2rem; }}
    .st-key-topbar > div:has(> [data-testid="stSpace"]), .st-key-topbar [data-testid="stSpace"] {{ display: none !important; }}
    .st-key-nav-brand, .st-key-topbar > div:has(.st-key-nav-brand) {{ order: 1; }}
    .st-key-nav-more, .st-key-topbar > div:has(.st-key-nav-more) {{ order: 2; margin-left: auto; }}
    .st-key-topbar > div:has(.st-key-nav-steps) {{ order: 3; width: 100% !important; }}
    .st-key-nav-steps {{ width: 100% !important; order: 3; justify-content: space-between; flex-wrap: nowrap !important; }}
    [class*="st-key-navstep-"] {{ min-width: 0; }}
    .st-key-nav-steps > div:has(.jd-nav-rule) {{ display: none !important; }}
    .st-key-topbar [data-testid="stPageLink"] a p {{ font-size: 0.72rem !important; }}
    [class*="st-key-navstep-"] [data-testid="stPageLink"] a p::before {{ margin-right: 4px; }}
    .jd-nav-rule {{ display: none; }}
}}

/* 시작 화면 */
.jd-hero {{ text-align: center; padding: 8vh 0 0.6rem; }}
.jd-hero h1 {{ font-size: clamp(2.1rem, 5vw, 3.3rem); line-height: 1.22; letter-spacing: -0.05em; color: {INK}; margin: 0; font-weight: 760; }}
.jd-hero p.lede {{ color: {MUTED}; margin: 1rem 0 0; font-size: 1.02rem; }}
.jd-steps {{ display: flex; justify-content: center; gap: 0; margin: 2.4rem auto 0.4rem; max-width: 560px; }}
.jd-steps div {{ flex: 1; text-align: center; position: relative; color: {MUTED}; font-size: 0.82rem; }}
.jd-steps div::before {{ content: ""; display: block; width: 11px; height: 11px; margin: 0 auto 8px; border: 1px solid #838477; border-radius: 50%; background: #080808; position: relative; z-index: 1; }}
.jd-steps div + div::after {{ content: ""; position: absolute; top: 5px; right: 50%; width: 100%; height: 1px; background: #45473E; }}
.jd-steps div.on {{ color: {INK}; font-weight: 700; }}
.jd-steps div.on::before, .jd-steps div.done::before {{ background: {LIME}; border-color: {LIME}; }}
.jd-steps div.on::before {{ box-shadow: 0 0 10px #d9f47788; }}
.jd-hero-sub {{ text-align: center; color: {MUTED}; font-size: 0.86rem; margin-top: 0.2rem; }}
.st-key-hero-start {{ justify-content: center; }}
.st-key-hero-start button {{ background: {LIME} !important; border-color: {LIME} !important; border-radius: 10px !important; min-height: 3rem; min-width: 8rem; padding: 0 1.6rem; }}
.st-key-hero-start button p {{ color: #192008 !important; font-weight: 740; font-size: 1.02rem; }}

{_CARD_CSS}
{_CTA}
.jd-tile {{
    width: 3.2rem; height: 3.2rem; border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.5rem; line-height: 1;
}}
.jd-big {{ font-size: 2.6rem; font-weight: 780; color: {INK}; line-height: 1.05; letter-spacing: -0.03em; margin: 0.2rem 0 0; }}
.jd-hero-emoji {{ font-size: 6rem; line-height: 1; text-align: center; padding-top: 0.5rem; }}

/* 버튼: 기본은 어두운 알약, 주요 버튼은 라임 */
[data-testid="stBaseButton-primary"] {{ background: {LIME} !important; border-color: {LIME} !important; box-shadow: 0 2px 6px rgba(38,52,19,.15); }}
[data-testid="stBaseButton-primary"] p, [data-testid="stBaseButton-primary"] span {{ color: {LIME_INK} !important; font-weight: 730; }}
[data-testid="stBaseButton-primary"]:hover {{ filter: brightness(1.05); }}
[data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-secondaryFormSubmit"] {{ background: #181A14 !important; border-color: {RULE2} !important; }}
[data-testid="stBaseButton-secondary"] p {{ color: {INK} !important; font-weight: 650; }}
[data-testid="stBaseButton-secondary"]:hover {{ border-color: {LIME} !important; }}
[data-testid="stBaseButton-primaryFormSubmit"] {{ background: {LIME} !important; border-color: {LIME} !important; }}
[data-testid="stBaseButton-primaryFormSubmit"] p {{ color: {LIME_INK} !important; font-weight: 740; }}

/* 직무 고르기 옵션 카드 */
[class*="st-key-card-white-opt-"] {{ border: 1px solid {RULE2}; }}
.jd-opt-head {{ display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.1rem; }}
.jd-opt-num {{
    width: 1.9rem; height: 1.9rem; border-radius: 999px; background: {LIME}; color: {LIME_INK};
    display: inline-flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.95rem;
}}
.jd-opt-title {{ font-size: 1.25rem; font-weight: 780; color: {INK}; letter-spacing: -0.03em; }}

/* 선택된 pill·세그먼트: 라임 바탕 */
[data-testid="stBaseButton-pillsActive"], [data-testid="stBaseButton-segmented_controlActive"] {{
    background: {LIME} !important; color: {LIME_INK} !important; border-color: {LIME} !important;
}}
[data-testid="stBaseButton-pillsActive"] p, [data-testid="stBaseButton-segmented_controlActive"] p {{ color: {LIME_INK} !important; font-weight: 700; }}
[data-testid="stBaseButton-pills"], [data-testid="stBaseButton-segmented_control"] {{ background: {PANEL2} !important; border-color: {RULE2} !important; }}
[data-testid="stBaseButton-pills"] p, [data-testid="stBaseButton-segmented_control"] p {{ color: #F5F3EA !important; }}

[data-testid="stButtonGroup"] button[aria-checked="true"], [data-testid="stButtonGroup"] button[aria-pressed="true"] {{ background: {LIME} !important; border-color: {LIME} !important; }}
[data-testid="stButtonGroup"] button[aria-checked="true"] p, [data-testid="stButtonGroup"] button[aria-pressed="true"] p {{ color: {LIME_INK} !important; font-weight: 700; }}

/* 결과지·종합 박스 */
[class*="st-key-pf-report"], [class*="st-key-future-synth"] {{
    background: #0F100D; border: 1px solid {RULE2}; border-radius: 22px; padding: 1.7rem 1.8rem;
    box-shadow: 0 0 0 1px rgba(217,244,119,.06), 0 18px 48px rgba(0,0,0,.35);
}}
[class*="st-key-pf-report"] [class*="st-key-card-white-"], [class*="st-key-future-synth"] [class*="st-key-card-white-"] {{ border-color: {RULE}; background: {PANEL2}; }}
.jd-report-tag {{ display: inline-block; background: {LIME}; color: {LIME_INK}; font-weight: 760; font-size: 0.86rem;
    padding: 0.3rem 0.8rem; border-radius: 999px; }}
[class*="st-key-pf-next"] {{ background: {PANEL2}; border: 1px solid {RULE}; border-radius: 14px; padding: 0.9rem 1.1rem; }}

/* 간이검사 문항: 다섯 칸을 한 줄 막대로 */
[class*="st-key-pfq-row-"] {{ padding: 0.6rem 0 0.9rem; border-bottom: 1px solid #1F201B; }}
.jd-q {{ font-size: 1.04rem; font-weight: 700; color: {INK}; line-height: 1.5; display: flex; gap: 0.5rem; align-items: baseline; }}
.jd-q-num {{ flex: none; color: {MUTED}; font-size: 0.98rem; font-weight: 700; }}
[class*="st-key-pfq-row-"] [data-testid="stButtonGroup"] > div {{ gap: 0 !important; background: {PANEL2}; border: 1px solid #414337; border-radius: 11px; overflow: hidden; width: 100%; flex-wrap: nowrap !important; }}
[class*="st-key-pfq-row-"] [data-testid="stButtonGroup"] button {{
    flex: 1 1 0; min-height: 2.6rem; border: 0 !important; border-radius: 0 !important; background: transparent !important;
    border-right: 1px solid #2B2C25 !important;
}}
[class*="st-key-pfq-row-"] [data-testid="stButtonGroup"] button:last-child {{ border-right: 0 !important; }}
[class*="st-key-pfq-row-"] [data-testid="stButtonGroup"] button p {{ font-size: 0.86rem; font-weight: 560; color: #DAD8CE !important; }}
[class*="st-key-pfq-row-"] [data-testid="stButtonGroup"] button[aria-checked="true"],
[class*="st-key-pfq-row-"] [data-testid="stButtonGroup"] button[aria-pressed="true"],
[class*="st-key-pfq-row-"] [data-testid="stBaseButton-segmented_controlActive"] {{ background: {LIME} !important; }}
[class*="st-key-pfq-row-"] [data-testid="stButtonGroup"] button[aria-checked="true"] p,
[class*="st-key-pfq-row-"] [data-testid="stButtonGroup"] button[aria-pressed="true"] p,
[class*="st-key-pfq-row-"] [data-testid="stBaseButton-segmented_controlActive"] p {{ color: {LIME_INK} !important; font-weight: 760; }}
[class*="st-key-pfq-row-"] [data-testid="stButtonGroup"] button:hover {{ background: #1D2016 !important; }}
@media (max-width: 640px) {{
    [class*="st-key-pfq-row-"] [data-testid="stButtonGroup"] button {{ min-height: 2.5rem; padding: 0.2rem 0.1rem; }}
    [class*="st-key-pfq-row-"] [data-testid="stButtonGroup"] button p {{ font-size: 0.7rem; letter-spacing: -0.04em; white-space: nowrap; }}
    .jd-q {{ font-size: 0.98rem; }}
}}

/* 단계 탭·진행 막대 */
.jd-stage {{ display: flex; gap: 1.2rem; border-bottom: 1px solid {RULE}; margin-bottom: 0.6rem; }}
.jd-stage span {{ padding: 0.45rem 0; font-size: 0.88rem; color: {MUTED}; font-weight: 600; }}
.jd-stage span.on {{ color: {INK}; border-bottom: 2px solid {LIME}; font-weight: 760; }}
.jd-stage span.done {{ color: #CFE58A; }}
.jd-progress {{ display: flex; justify-content: space-between; color: {MUTED}; font-size: 0.86rem; border-top: 1px solid {RULE}; padding-top: 0.6rem; }}
.jd-progress b {{ color: {INK}; }}
.jd-bar {{ height: 3px; background: #24251F; border-radius: 9px; margin: 0.35rem 0 0.4rem; overflow: hidden; }}
.jd-bar i {{ display: block; height: 100%; background: {LIME}; }}

/* 채팅 입력창 */
[data-testid="stChatInput"] {{ background: {PANEL2} !important; border: 1px solid {RULE2} !important; border-radius: 16px !important; box-shadow: 0 6px 24px rgba(0,0,0,.35); }}
[data-testid="stChatInput"] textarea {{ color: {INK} !important; font-size: 1rem; background: transparent !important; min-height: 3rem; }}
[data-testid="stChatInput"] > div, [data-testid="stChatInput"] div[data-baseweb] {{ background: transparent !important; }}
[data-testid="stChatInput"] textarea::placeholder {{ color: #8E8C82 !important; opacity: 1; }}
[data-testid="stChatInputSubmitButton"] {{ background: {LIME} !important; border-radius: 999px !important; }}
[data-testid="stChatInputSubmitButton"] svg {{ fill: {LIME_INK} !important; color: {LIME_INK} !important; }}
[data-testid="stChatInput"]:focus-within {{ border-color: {LIME} !important; box-shadow: 0 0 0 3px rgba(217,244,119,.15); }}
[data-testid="stBottom"] > div {{ background: linear-gradient(to top, #080808 70%, rgba(8,8,8,0)); border-top: 1px solid #1C1D18; }}
@keyframes jdPulse {{
    0%, 100% {{ box-shadow: 0 0 0 0 rgba(217,244,119,.35); }}
    50% {{ box-shadow: 0 0 0 8px rgba(217,244,119,0); }}
}}

/* 채팅 말풍선 */
[data-testid="stChatMessage"] {{ background: {PANEL}; border: 1px solid {RULE}; border-radius: 16px; padding: 1rem 1.2rem; margin-bottom: 0.7rem; }}
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {{ color: {INK}; line-height: 1.72; }}
[data-testid="stChatMessage"] [data-testid="stCaptionContainer"] p {{ color: {MUTED}; line-height: 1.5; }}

/* 입력칸·펼침·탭 */
[data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="textarea"] {{ background: {PANEL2} !important; border-color: {RULE2} !important; }}
[data-testid="stExpander"] details {{ background: {PANEL}; border-color: {RULE} !important; border-radius: 14px; }}
[data-testid="stTabs"] [aria-selected="true"] p {{ color: {INK} !important; font-weight: 760; }}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {{ background: {LIME} !important; }}
[data-testid="stAlert"] {{ border-radius: 12px; }}

/* 담은 직무·방법 카드 */
[class*="st-key-method-"] button {{ min-height: 4.2rem; justify-content: flex-start; text-align: left; border-radius: 12px !important; }}
[class*="st-key-method-"][class*="-on"] button {{ border-color: {LIME} !important; background: #1A1E10 !important; }}
[class*="st-key-method-"][class*="-on"] button p {{ color: #E7F8AD !important; }}
[class*="st-key-jobrow-"] {{ border-bottom: 1px solid {RULE}; padding: 0.55rem 0; }}
[class*="st-key-picked-bar"] {{ background: #10120C; border: 1px solid #3B4226; border-radius: 14px; padding: 0.8rem 1rem; }}
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
