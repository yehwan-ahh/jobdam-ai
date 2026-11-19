"""AI 답변 생성 (공급자 교체 가능, 기본은 OpenAI).

키 우선순위
1. 사용자가 사이드바에 넣은 '내 API 키'(BYOK) — st.session_state에만 두고 저장·기록하지 않습니다.
2. 팀 키 — st.secrets의 공급자별 키(OPENAI_API_KEY 등). 세션당 질문 수를 LLM_SESSION_LIMIT(기본 20)로 제한합니다.
3. 둘 다 없으면 None → 화면은 시연 모드로 동작합니다.

secrets 예시
    LLM_PROVIDER = "openai"         # openai(기본) | anthropic
    LLM_MODEL = "gpt-5-mini"        # OpenAI 요금표에서 확인 후 바꿀 수 있습니다
    OPENAI_API_KEY = "sk-..."
    LLM_SESSION_LIMIT = "20"

새 공급자를 추가하려면 _PROVIDERS에 (표시이름, secrets 키 이름, 기본 모델, 호출 함수)를 등록하면 됩니다.
"""

from collections.abc import Callable
from dataclasses import dataclass

import streamlit as st

from utils.secrets import get_secret

BYOK_STATE_KEY = "byok_api_key"
USAGE_STATE_KEY = "llm_team_key_used"


@dataclass
class LLMResult:
    text: str | None
    error: str | None = None  # 사용자에게 보여 줄 안내 문구


Caller = Callable[..., LLMResult]


# ── 공급자별 호출 ────────────────────────────────────────────
def _call_openai(
    api_key: str, model_name: str, system: str, messages: list[dict[str, str]], json_mode: bool = False
) -> LLMResult:
    import openai

    client = openai.OpenAI(api_key=api_key, max_retries=2, timeout=60.0)
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": system}, *messages],  # type: ignore[list-item]
            max_completion_tokens=4000,
            **({"response_format": {"type": "json_object"}} if json_mode else {}),
        )
    except openai.AuthenticationError:
        return LLMResult(None, "API 키가 올바르지 않아요. 키를 다시 확인해 주세요.")
    except openai.RateLimitError:
        return LLMResult(None, "요청이 많거나 사용 한도에 닿았어요. 조금 뒤에 다시 물어봐 주세요.")
    except openai.APIStatusError as e:
        return LLMResult(None, f"AI 서비스 오류가 났어요 ({e.status_code}). 잠시 뒤 다시 시도해 주세요.")
    except openai.APIConnectionError:
        return LLMResult(None, "AI 서비스에 연결하지 못했어요. 네트워크를 확인해 주세요.")

    choice = response.choices[0] if response.choices else None
    message = choice.message if choice else None
    if message is not None and getattr(message, "refusal", None):
        return LLMResult(None, "이 질문에는 답하기 어려워요. 진로·직무와 관련된 질문으로 바꿔 주세요.")
    text = (message.content or "").strip() if message else ""
    return LLMResult(text or None, None if text else "답변이 비어 있어요. 다시 시도해 주세요.")


def _call_anthropic(
    api_key: str, model_name: str, system: str, messages: list[dict[str, str]], json_mode: bool = False
) -> LLMResult:
    del json_mode  # 프롬프트로 JSON 형식을 요구합니다
    try:
        import anthropic
    except ImportError:
        return LLMResult(None, "Claude를 쓰려면 requirements.txt에 anthropic 패키지를 추가해야 해요.")

    client = anthropic.Anthropic(api_key=api_key, max_retries=2, timeout=60.0)
    try:
        response = client.beta.messages.create(
            model=model_name,
            max_tokens=4000,
            system=system,
            messages=messages,  # type: ignore[arg-type]
            output_config={"effort": "low"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
    except anthropic.AuthenticationError:
        return LLMResult(None, "API 키가 올바르지 않아요. 키를 다시 확인해 주세요.")
    except anthropic.RateLimitError:
        return LLMResult(None, "요청이 많아 잠시 쉬어 가요. 조금 뒤에 다시 물어봐 주세요.")
    except anthropic.APIStatusError as e:
        return LLMResult(None, f"AI 서비스 오류가 났어요 ({e.status_code}). 잠시 뒤 다시 시도해 주세요.")
    except anthropic.APIConnectionError:
        return LLMResult(None, "AI 서비스에 연결하지 못했어요. 네트워크를 확인해 주세요.")

    if response.stop_reason == "refusal":
        return LLMResult(None, "이 질문에는 답하기 어려워요. 진로·직무와 관련된 질문으로 바꿔 주세요.")
    text = "".join(block.text for block in response.content if block.type == "text").strip()
    return LLMResult(text or None, None if text else "답변이 비어 있어요. 다시 시도해 주세요.")


# 이름: (표시이름, 팀 키 secrets 이름, 기본 모델, 호출 함수, 키 예시)
_PROVIDERS: dict[str, tuple[str, str, str, Caller, str]] = {
    "openai": ("OpenAI", "OPENAI_API_KEY", "gpt-5-mini", _call_openai, "sk-..."),
    "anthropic": ("Claude (Anthropic)", "ANTHROPIC_API_KEY", "claude-opus-5-5", _call_anthropic, "sk-ant-..."),
}
DEFAULT_PROVIDER = "openai"


# ── 설정 읽기 ───────────────────────────────────────────────
def provider() -> str:
    name = (get_secret("LLM_PROVIDER") or DEFAULT_PROVIDER).lower()
    return name if name in _PROVIDERS else DEFAULT_PROVIDER


def provider_label() -> str:
    return _PROVIDERS[provider()][0]


def model() -> str:
    return get_secret("LLM_MODEL") or _PROVIDERS[provider()][2]


def _team_key() -> str | None:
    return get_secret(_PROVIDERS[provider()][1])


def _byok_key() -> str | None:
    value = st.session_state.get(BYOK_STATE_KEY)
    return value.strip() if isinstance(value, str) and value.strip() else None


def _session_limit() -> int:
    try:
        return int(get_secret("LLM_SESSION_LIMIT") or 20)
    except ValueError:
        return 20


def key_source() -> str | None:
    """'byok' | 'team' | None"""
    if _byok_key():
        return "byok"
    if _team_key():
        return "team"
    return None


def is_enabled() -> bool:
    return key_source() is not None


def remaining_team_questions() -> int:
    return max(0, _session_limit() - int(st.session_state.get(USAGE_STATE_KEY, 0)))


# ── 생성 ────────────────────────────────────────────────────
def generate(system: str, messages: list[dict[str, str]], json_mode: bool = False) -> LLMResult:
    """messages: [{"role": "user"|"assistant", "content": str}, ...]"""
    source = key_source()
    if source is None:
        return LLMResult(None, "AI 키가 없어 시연 모드로 답하고 있어요.")
    if source == "team" and remaining_team_questions() <= 0:
        return LLMResult(
            None, "이번 접속에서 쓸 수 있는 질문 수를 모두 썼어요. 사이드바에 내 API 키를 넣으면 계속할 수 있어요."
        )

    api_key = _byok_key() if source == "byok" else _team_key()
    call = _PROVIDERS[provider()][3]
    result = call(api_key or "", model(), system, messages, json_mode=json_mode)
    if result.text is not None and source == "team":
        st.session_state[USAGE_STATE_KEY] = int(st.session_state.get(USAGE_STATE_KEY, 0)) + 1
    return result


def render_byok_sidebar() -> None:
    """사이드바의 '내 API 키 쓰기'. 키는 이 세션 메모리에만 있고 저장되지 않습니다."""
    label, _, _, _, example = _PROVIDERS[provider()]
    with st.sidebar.expander("내 API 키 쓰기", icon=":material/key:"):
        st.text_input(
            f"{label} API 키",
            type="password",
            key=BYOK_STATE_KEY,
            placeholder=example,
            help="브라우저 창을 닫으면 사라지며, 서버에 저장하거나 기록하지 않아요.",
        )
        source = key_source()
        if source == "byok":
            st.caption(":green[:material/check:] 내 키로 답변해요.")
        elif source == "team":
            st.caption(f"팀 키 사용 중 · 남은 질문 {remaining_team_questions()}개")
        else:
            st.caption("키가 없어서 시연 모드로 보여 줘요.")


def generate_json(system: str, messages: list[dict[str, str]]) -> tuple[dict | None, str | None]:
    """JSON 객체로 답을 받습니다. (데이터, 오류 안내)"""
    import json
    import re

    result = generate(system, messages, json_mode=True)
    if not result.text:
        return None, result.error
    text = result.text.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    try:
        data = json.loads(match.group(0) if match else text)
    except (ValueError, AttributeError):
        return None, "추천 결과를 읽지 못했어요. 다시 한 번 물어봐 주세요."
    return (data if isinstance(data, dict) else None), None
