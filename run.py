#!/usr/bin/env python3
"""battery-repro 진입점.

**이것이 유일한 공식 진입점입니다.** Windows 에 ``make`` 가 없습니다
(Git for Windows 에도 없습니다). ``Makefile`` 은 각 타깃이 이 파일을
호출하기만 하는 껍데기이며 macOS · Linux 편의용입니다.

    python run.py notebook     jupyter lab 실행 (실제 작업은 여기서)
    python run.py check        LOCK 대조
    python run.py lock-init    현재 상태로 LOCK.md 채우기
    python run.py anchors      코드 앵커 유효성 확인
    python run.py claims       registry 검증 → findings/PAPER_CODE_MAP.md 재생성
    python run.py data-list    받을 데이터 목록 (다운로드 안 함)
    python run.py papers       arXiv PDF 3편

이 파일은 표준 라이브러리만 씁니다. 조원은 clone 만 하므로, 아무것도
설치하지 않은 상태에서도 ``check`` · ``anchors`` · ``claims`` 가 돌아가야
합니다. 노트북에서 쓰는 numpy · pandas 는 그때 필요합니다.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# 한국어 Windows 콘솔의 기본 인코딩이 cp949 라, 이 줄이 없으면 한국어 출력에
# 섞인 문자 하나로 UnicodeEncodeError 가 나며 죽습니다. PYTHONIOENCODING
# 설정에 기대지 않습니다 — 조원이 README 의 그 절을 건너뛰어도 돌아가야 합니다.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError, ValueError):
        pass


def _rule(title: str) -> None:
    print(f"\n=== {title} " + "=" * max(0, 60 - len(title)))


# ---------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------

def cmd_check(args) -> int:
    from verify import lock

    _rule("LOCK 대조")
    result = lock.check()
    print(lock.format_report(result))
    return 1 if result["broken_layers"] else 0


# ---------------------------------------------------------------------------
# lock-init
# ---------------------------------------------------------------------------

def cmd_lock_init(args) -> int:
    from datetime import datetime

    from verify import lock

    _rule("LOCK 채우기")
    stamp = args.stamp or datetime.now().strftime("%Y-%m-%d")
    result = lock.init(stamp=stamp, author=args.author or "")

    for item, value in result["filled"]:
        print(f"  채움    {item}  =  {value}")
    for item, reason in result["skipped"]:
        print(f"  남김    {item}  ({reason})")

    print(f"\n환경 기록: {result['env_lock']}")
    if result["skipped"]:
        print(
            "\n(미정) 이 남아 있습니다. **이 상태로 태그를 찍지 마십시오.**\n"
            "데이터를 받고 노트북(00 → 01 → 02 → 03)을 돌린 뒤 다시 실행하십시오."
        )
    else:
        print("\n모든 digest 항목이 찼습니다. 이제 커밋하고 태그를 찍어도 됩니다.")
    return 0


# ---------------------------------------------------------------------------
# anchors
# ---------------------------------------------------------------------------

def cmd_anchors(args) -> int:
    from verify import anchors

    _rule("코드 앵커")
    rows = anchors.check()
    print(anchors.format_report(rows))
    bad = [row for row in rows if row["status"] in (anchors.STATUS_CHANGED, anchors.STATUS_LOST)]
    return 1 if bad else 0


# ---------------------------------------------------------------------------
# claims
# ---------------------------------------------------------------------------

def cmd_claims(args) -> int:
    from verify import render

    _rule("registry 검증")
    result = render.render_all(write=not args.dry_run)

    print(f"레코드 {result['records']}개")
    if result["problems"]:
        print(f"\n기록 요건 위반 {len(result['problems'])}건:")
        for problem in result["problems"]:
            print(f"  - {problem}")
    else:
        print("기록 요건 위반 없음")

    if args.dry_run:
        print("\n(--dry-run: 문서를 쓰지 않았습니다)")
    else:
        print(f"\n생성: {result['map_path'].relative_to(REPO_ROOT).as_posix()}")
        print(f"생성: {result['open_path'].relative_to(REPO_ROOT).as_posix()}")
    return 1 if result["problems"] else 0


# ---------------------------------------------------------------------------
# data-list
# ---------------------------------------------------------------------------

def cmd_data_list(args) -> int:
    from verify import load_config, read_text

    manifest = REPO_ROOT / "manifests" / "data_md5.txt"
    _rule("받을 데이터")

    print("Zenodo record 21149533 (BatteryLife_Processed v12, 인증 불필요)")
    print("  https://zenodo.org/records/21149533")
    print("\n이 명령은 목록만 보여줍니다. **다운로드는 사람이 합니다.**\n")

    # 파일명에 공백이 있습니다 ("Life labels.zip"). 공백으로 자르면 깨지므로
    # md5 토큰을 기준으로 잡습니다.
    import re

    row_pattern = re.compile(
        r"^(?P<set>labels|core|full)\s+"
        r"(?P<file>.+?)\s+"
        r"(?P<md5>[0-9a-f]{32}|\(미확인\))\s+"
        r"(?P<size>\S+)"
        r"(?:\s+(?P<note>.*))?$"
    )

    rows = []
    for line in read_text(manifest).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = row_pattern.match(line)
        if not match:
            continue
        rows.append({
            "set": match.group("set"), "file": match.group("file"),
            "md5": match.group("md5"), "size": match.group("size"),
            "note": match.group("note") or "",
        })

    wanted = args.set or "labels"
    order = {"labels": 0, "core": 1, "full": 2}
    shown = [r for r in rows if wanted == "all" or r["set"] == wanted]

    config = load_config()
    zenodo_dir = config.get("ZENODO_DIR", "")
    have_dir = Path(zenodo_dir) if zenodo_dir else None

    width = max((len(r["file"]) for r in shown), default=10)
    for row in sorted(shown, key=lambda r: (order.get(r["set"], 9), r["file"])):
        present = ""
        if have_dir is not None:
            present = " [있음]" if (have_dir / row["file"]).exists() else " [없음]"
        print(f"  {row['set']:6} {row['file'].ljust(width)}  {row['md5']}"
              f"  {row['size']}{present}")
        if row["note"] and args.verbose:
            print(f"         {row['note']}")

    print(f"\n{len(shown)}개 ({wanted} 세트)")
    print("\n세트: labels(라벨 검증 최소 집합) / core / full / all")
    print("용량은 (미확인) 입니다. Zenodo Files 표에서 확인해")
    print("manifests/data_md5.txt 헤더에 다운로드 용량과 해제 후 용량을 **따로** 적으십시오.")
    print("\nHuggingFace(processed_SOH) 는 게이트 저장소라 이 하니스가 건드리지 않습니다.")
    return 0


# ---------------------------------------------------------------------------
# papers
# ---------------------------------------------------------------------------

def cmd_papers(args) -> int:
    import importlib.util

    _rule("논문 PDF")
    # papers/ 를 패키지로 만들지 않기 위해 경로로 직접 읽습니다.
    path = REPO_ROOT / "papers" / "fetch.py"
    spec = importlib.util.spec_from_file_location("papers_fetch", path)
    fetch = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fetch)
    return fetch.main(list_only=args.list_only)


# ---------------------------------------------------------------------------
# notebook
# ---------------------------------------------------------------------------

def cmd_notebook(args) -> int:
    _rule("jupyter lab")
    command = [sys.executable, "-m", "jupyter", "lab"]
    print("실행:", " ".join(command))
    print("작업 디렉터리:", REPO_ROOT)
    print("\n노트북 순서: 00 → 01 → 02 → 03")
    print("출력은 지운 상태로 커밋합니다 (nbstripout).")
    try:
        return subprocess.call(command, cwd=str(REPO_ROOT))
    except FileNotFoundError:
        print(
            "\njupyter 를 찾지 못했습니다. 설치하십시오:\n"
            "    python -m pip install -r requirements.txt",
            file=sys.stderr,
        )
        return 1


# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run.py",
        description="battery-repro — 상위 저장소 코드의 동작을 확정하는 하니스",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "논문 재현이 아닙니다. 논문은 정답지가 아니라 비교 대상입니다.\n"
            "값이 배포물·논문과 갈리는 것은 실패가 아니라 발견입니다.\n"
            "어느 셀이 어떻게 다른지 못 짚는 것이 실패입니다."
        ),
    )
    sub = parser.add_subparsers(dest="command", metavar="<명령>")

    sub.add_parser("check", help="LOCK 대조").set_defaults(func=cmd_check)

    lock_init = sub.add_parser("lock-init", help="현재 상태로 LOCK.md 채우기")
    lock_init.add_argument("--author", default="", help="LOCK.md 의 생성자")
    lock_init.add_argument("--stamp", default="", help="생성 날짜 (기본: 오늘)")
    lock_init.set_defaults(func=cmd_lock_init)

    sub.add_parser("anchors", help="코드 앵커 유효성 확인").set_defaults(func=cmd_anchors)

    claims = sub.add_parser("claims", help="registry 검증 → PAPER_CODE_MAP.md 재생성")
    claims.add_argument("--dry-run", action="store_true", help="검증만 하고 쓰지 않음")
    claims.set_defaults(func=cmd_claims)

    data_list = sub.add_parser("data-list", help="받을 데이터 목록 (다운로드 안 함)")
    data_list.add_argument("--set", choices=["labels", "core", "full", "all"],
                           help="기본: labels")
    data_list.add_argument("-v", "--verbose", action="store_true", help="비고까지")
    data_list.set_defaults(func=cmd_data_list)

    papers = sub.add_parser("papers", help="arXiv PDF 3편")
    papers.add_argument("--list", dest="list_only", action="store_true",
                        help="받지 않고 목록만")
    papers.set_defaults(func=cmd_papers)

    sub.add_parser("notebook", help="jupyter lab 실행").set_defaults(func=cmd_notebook)
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    return args.func(args) or 0


if __name__ == "__main__":
    raise SystemExit(main())
