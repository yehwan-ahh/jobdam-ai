"""성공한 결과만 캐시합니다.

st.cache_data는 실패 결과(None, (None, 오류))까지 그대로 저장해서, 공공 API가 한 번 잠깐 실패하면
그 기능이 캐시 기간(최대 하루) 내내 꺼진 것처럼 보였어요. 실패는 예외로 바꿔 캐시하지 않고,
다음 요청 때 다시 시도하게 합니다.
"""

import functools
from typing import Any, Callable

import streamlit as st


class _Fail(Exception):
    """캐시하지 않을 실패 결과를 실어 나르는 예외."""


def _failed(result: Any) -> bool:
    if result is None:
        return True
    return isinstance(result, tuple) and len(result) == 2 and result[0] is None


def cache_success(ttl: int) -> Callable:
    def deco(fn: Callable) -> Callable:
        def cached(*args, **kwargs):
            result = fn(*args, **kwargs)
            if _failed(result):
                raise _Fail(result)  # 예외는 캐시되지 않아요
            return result

        # 함수마다 캐시가 섞이지 않도록 이름을 원래 함수 기준으로
        cached.__module__ = fn.__module__
        cached.__qualname__ = f"{fn.__qualname__}__ok"
        cached.__name__ = f"{fn.__name__}__ok"
        stored = st.cache_data(ttl=ttl, show_spinner=False)(cached)

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return stored(*args, **kwargs)
            except _Fail as e:
                return e.args[0]

        wrapper.clear = stored.clear  # type: ignore[attr-defined]
        return wrapper

    return deco
