"""리디자인 시안 미리보기 — `/preview/` 하위에 design/ 폴더를 정적 서빙.

design/ 의 HTML 은 React UMD + Babel standalone 로 동작하는 자가 완결형
정적 시안이라 별도 번들링 없이 그대로 서빙하면 된다. 기존 페이지
(`/notices`, `/settings`) 와 분리된 prefix 라 본 도입 전 사이드바이사이드
검토용으로만 쓴다.
"""
from pathlib import Path

from flask import Blueprint, send_from_directory

_DESIGN_DIR = Path(__file__).resolve().parents[3] / "design"

bp = Blueprint("preview", __name__, url_prefix="/preview")


@bp.get("/")
def index():
    return send_from_directory(_DESIGN_DIR, "index.html")


@bp.get("/<path:filename>")
def asset(filename: str):
    return send_from_directory(_DESIGN_DIR, filename)
