"""st.secrets를 안전하게 읽습니다. secrets.toml이 없거나 키가 비어 있으면 None."""

import streamlit as st


def get_secret(name: str) -> str | None:
    try:
        value = st.secrets.get(name)
    except Exception:  # secrets.toml 자체가 없을 때
        return None
    if value is None:
        return None
    value = str(value).strip()
    return value or None
