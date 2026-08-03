"""train — 몇 시간 걸리는 것.

라벨 검증(``verify/``)과 달리 여기는 GPU 와 시간이 필요합니다.
**첫 태그 범위 밖입니다.** 자리만 잡아두고 비워둡니다.

Windows 에서는 **Git Bash 가 필요합니다.** 상위 학습 스크립트가 bash 파일
(``train_eval_scripts/*.sh``)이고 그것만은 바꿀 수 없기 때문입니다.
라벨 검증 경로는 순수 Python 이라 bash 없이 돌아갑니다.

    paths.py    하드코딩 절대경로 치환 (.build/ 에 사본)
    launch.py   백그라운드 실행
    collect.py  체크포인트 · 로그 → 지표 JSON
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
