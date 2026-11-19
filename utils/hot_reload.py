"""배포 후 utils 모듈이 예전 버전에 머무는 문제 방지.

Streamlit Cloud는 GitHub에 새 커밋이 오면 페이지 스크립트는 새로 읽지만,
이미 import된 utils 모듈은 프로세스를 재시작하기 전까지 예전 코드를 씁니다.
여기서 파일 수정 시각을 비교해, 바뀐 것이 있으면 utils 모듈을 의존 순서대로 다시 불러옵니다.
"""

import importlib
import os
import sys

# 의존성이 적은 것부터 (뒤의 모듈이 앞의 모듈을 import)
ORDER = [
    "utils.secrets",
    "utils.demo_data",
    "utils.style",
    "utils.prompts",
    "utils.careernet",
    "utils.kosis",
    "utils.worknet",
    "utils.majors",
    "utils.interviews",
    "utils.training",
    "utils.llm",
    "utils.evidence",
    "utils.status",
]
_MTIMES: dict[str, float] = {}


def _mtime(name: str) -> float | None:
    mod = sys.modules.get(name)
    path = getattr(mod, "__file__", None)
    try:
        return os.path.getmtime(path) if path else None
    except OSError:
        return None


def remember() -> None:
    """실행이 끝날 때 불러온 모듈의 수정 시각을 기억합니다(처음 본 모듈만)."""
    for name in ORDER:
        current = _mtime(name)
        if current is not None and name not in _MTIMES:
            _MTIMES[name] = current


def reload_if_changed() -> bool:
    changed = False
    for name in ORDER:
        current = _mtime(name)
        if current is None:
            continue
        if name in _MTIMES and _MTIMES[name] != current:
            changed = True
        _MTIMES[name] = current
    if changed:
        for name in ORDER:
            if name in sys.modules:
                importlib.reload(sys.modules[name])
                _MTIMES[name] = _mtime(name) or 0.0
    return changed
