# 선택 사항. macOS · Linux 편의용. 정식 진입점은 run.py 입니다.
#
# Windows 에는 make 가 없습니다 (Git for Windows 에도 없습니다).
# 이 파일의 각 타깃은 python run.py <명령> 을 호출하기만 합니다.
# 여기에 로직을 넣지 마십시오 — Windows 사용자가 못 씁니다.
#
# 들여쓰기는 탭입니다 (.editorconfig 참조).

PY ?= python

.PHONY: help notebook check lock-init anchors claims data-list papers

help:
	@echo "정식 진입점은 run.py 입니다. make 는 선택 사항입니다."
	@$(PY) run.py --help

notebook:
	$(PY) run.py notebook

check:
	$(PY) run.py check

lock-init:
	$(PY) run.py lock-init

anchors:
	$(PY) run.py anchors

claims:
	$(PY) run.py claims

data-list:
	$(PY) run.py data-list

papers:
	$(PY) run.py papers
