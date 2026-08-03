#!/usr/bin/env python3
"""arXiv 프리프린트 3편 내려받기.

    python run.py papers          받는다
    python run.py papers --list   목록만 본다

표준 라이브러리만 씁니다 (``requests`` 없이 ``urllib``). ``.sh`` 대신
``.py`` 인 이유는 Windows 에서 bash 없이 돌아가야 하기 때문입니다.

**PDF 는 .gitignore 대상입니다.** arXiv 프리프린트와 학회 게재본은
라이선스가 각기 달라 재배포가 불명확합니다. 각자 받으십시오.
자세한 것은 ``papers/SOURCES.md`` 를 보십시오.
"""

from __future__ import annotations

import sys
import urllib.error
import urllib.request
from pathlib import Path

PAPERS_DIR = Path(__file__).resolve().parent

# 한국어 Windows 콘솔은 기본이 cp949 입니다. 직접 실행될 때를 대비합니다
# (run.py 를 거치면 이미 되어 있습니다).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError, ValueError):
        pass

PAPERS = [
    {
        "name": "BatteryML",
        "arxiv": "2310.14714",
        "venue": "ICLR 2024",
        "doi": "",
    },
    {
        "name": "BatteryLife",
        "arxiv": "2502.18807",
        "venue": "KDD 2025",
        "doi": "10.1145/3711896.3737372",
    },
    {
        "name": "BatteryMFormer",
        "arxiv": "2605.27044",
        "venue": "KDD 2026",
        "doi": "",
    },
]

USER_AGENT = "battery-repro/1.0 (lab use; arXiv PDF fetch)"
TIMEOUT = 120


def target_path(paper: dict) -> Path:
    return PAPERS_DIR / f"{paper['arxiv']}_{paper['name']}.pdf"


def fetch_one(paper: dict) -> tuple:
    """(성공 여부, 메시지)."""
    destination = target_path(paper)
    if destination.exists() and destination.stat().st_size > 0:
        size = destination.stat().st_size / 1024
        return True, f"이미 있음 ({size:.0f} KB) — {destination.name}"

    url = f"https://arxiv.org/pdf/{paper['arxiv']}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            data = response.read()
    except urllib.error.HTTPError as error:
        return False, f"HTTP {error.code} — {url}"
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return False, f"내려받기 실패: {error} — {url}"

    if not data.startswith(b"%PDF"):
        return False, (
            f"PDF 가 아닙니다 ({len(data)} 바이트). arXiv 가 안내 페이지를 "
            f"돌려줬을 수 있습니다. 브라우저로 {url} 을 확인하십시오."
        )

    destination.write_bytes(data)
    return True, f"받음 ({len(data) / 1024:.0f} KB) — {destination.name}"


def main(list_only: bool = False) -> int:
    width = max(len(paper["name"]) for paper in PAPERS)

    if list_only:
        for paper in PAPERS:
            mark = "있음" if target_path(paper).exists() else "없음"
            doi = f"  DOI {paper['doi']}" if paper["doi"] else ""
            print(f"  [{mark}] {paper['name'].ljust(width)}  arXiv {paper['arxiv']}"
                  f"  {paper['venue']}{doi}")
        print(f"\n저장 위치: {PAPERS_DIR}")
        print("PDF 는 .gitignore 대상입니다. papers/SOURCES.md 를 보십시오.")
        return 0

    failed = 0
    for paper in PAPERS:
        ok, message = fetch_one(paper)
        print(f"  [{'ok' if ok else 'FAIL'}] {paper['name'].ljust(width)}  {message}")
        if not ok:
            failed += 1

    print(f"\n저장 위치: {PAPERS_DIR}")
    if failed:
        print(f"{failed}편을 받지 못했습니다. 위 URL 을 브라우저로 여십시오.",
              file=sys.stderr)
    else:
        print("메모는 papers/NOTES.md 에 남기십시오.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(list_only="--list" in sys.argv))
