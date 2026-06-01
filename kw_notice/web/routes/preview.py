"""리디자인 미리보기 — `/preview/` 하위에서 새 UI 를 실제 데이터/폼과 결합.

design/ 시안의 사본을 templates/preview, static/preview 에 두고 백엔드와 연결한다.
기존 /notices, /settings 라우트와 별개로 동작하며 같은 repository 를 공유한다.
settings 비즈니스 로직은 routes.settings 의 module-level 헬퍼를 그대로 import 해
중복 구현을 피한다.
"""
import sqlite3
from datetime import datetime

from flask import (
    Blueprint, Response, flash, get_flashed_messages, redirect, render_template,
    request, url_for,
)

from ... import config, db
from ...crawler.parser import ParsedNotice
from ...notifier.discord import DiscordChannel
from ...repository import notices as notices_repo
from ...repository import settings as settings_repo
from ...repository import users as users_repo
from .settings import (
    ERROR_MESSAGES,
    FREQUENCY_ID_TO_NAME,
    _grid_times,
    _parse_frequency_mode,
    _parse_is_active,
    _parse_selected_times,
    _validate_times,
)

bp = Blueprint("preview", __name__, url_prefix="/preview")


def _shared_urls() -> dict:
    return {
        "notices": url_for("preview.notices_index"),
        "settings": url_for("preview.settings_index"),
        "save": url_for("preview.settings_save"),
        "times_add": url_for("preview.times_add_grid"),
        "times_add_save": url_for("preview.times_add_save"),
        "times_delete": url_for("preview.times_delete"),
        "test_send": url_for("preview.test_send"),
    }


def _serialize_notices(rows) -> list[dict]:
    return [
        {
            "duid": int(r["duid"]),
            "category_name": r["category_name"],
            "title": r["title"],
            "author": r["author"],
            "posted_date": r["posted_date"],
            "modified_date": r["modified_date"],
            "is_pinned": bool(r["is_pinned"]),
            "has_attachment": bool(r["has_attachment"]),
            "url": r["url"],
        }
        for r in rows
    ]


@bp.get("/")
def notices_index() -> str:
    with db.transaction() as conn:
        rows = notices_repo.list_recent(conn, limit=100)
    preload = {
        "notices": _serialize_notices(rows),
        "last_fetched_at": datetime.now().strftime("%H:%M"),
        "urls": _shared_urls(),
        "flashes": get_flashed_messages(),
        "error_messages": ERROR_MESSAGES,
    }
    return render_template("preview/notices.html", preload=preload)


@bp.get("/settings")
def settings_index() -> str:
    with db.transaction() as conn:
        settings = settings_repo.load(conn)
        custom_times = settings_repo.list_custom_times_with_id(
            conn, config.DEFAULT_USER_ID)
    preload = {
        "settings": {
            "frequency_mode": FREQUENCY_ID_TO_NAME[settings.frequency_mode],
            "is_active": settings.is_active,
            "custom_times": [{"id": cid, "t": t} for cid, t in custom_times],
        },
        "urls": _shared_urls(),
        "flashes": get_flashed_messages(),
        "error_messages": ERROR_MESSAGES,
    }
    return render_template("preview/settings.html", preload=preload)


@bp.post("/settings")
def settings_save() -> Response:
    mode_id = _parse_frequency_mode(request.form)
    is_active = _parse_is_active(request.form)
    if mode_id is None:
        flash("error.invalid_frequency_mode")
        return redirect(url_for("preview.settings_index"))
    with db.transaction() as conn:
        settings_repo.update(conn, config.DEFAULT_USER_ID, mode_id, is_active)
    return redirect(url_for("preview.settings_index"))


@bp.get("/settings/times/add")
def times_add_grid() -> str:
    with db.transaction() as conn:
        settings = settings_repo.load(conn)
    preload = {
        "grid": _grid_times(),
        "registered": sorted(settings.custom_times),
        "urls": _shared_urls(),
        "flashes": get_flashed_messages(),
        "error_messages": ERROR_MESSAGES,
    }
    return render_template("preview/settings_times_add.html", preload=preload)


@bp.post("/settings/times/add")
def times_add_save() -> Response:
    candidates = _parse_selected_times(request.form)
    if not candidates:
        flash("error.no_time_selected")
        return redirect(url_for("preview.times_add_grid"))
    with db.transaction() as conn:
        settings = settings_repo.load(conn)
        existing = set(settings.custom_times)
        valid, err = _validate_times(candidates, existing)
        if err is not None:
            flash(err)
            return redirect(url_for("preview.times_add_grid"))
        try:
            settings_repo.add_custom_times(
                conn, config.DEFAULT_USER_ID, valid or [])
        except sqlite3.IntegrityError:
            flash("error.time_conflict")
            return redirect(url_for("preview.times_add_grid"))
    return redirect(url_for("preview.settings_index"))


@bp.post("/settings/times/delete")
def times_delete() -> Response:
    try:
        cid = int(request.form["id"])
    except (KeyError, ValueError):
        return redirect(url_for("preview.settings_index"))
    with db.transaction() as conn:
        settings_repo.delete_custom_time(conn, config.DEFAULT_USER_ID, cid)
    return redirect(url_for("preview.settings_index"))


@bp.post("/settings/test-send")
def test_send() -> Response:
    """기존 settings.test_send 와 동일 로직 — 운영시간·is_active 무관 즉시 발송."""
    with db.transaction() as conn:
        webhook = users_repo.get_discord_webhook(conn, config.DEFAULT_USER_ID)
        if webhook is None:
            flash("error.test_send_no_webhook")
            return redirect(url_for("preview.settings_index"))
        rows = notices_repo.list_recent(conn, limit=1)
    if not rows:
        flash("error.test_send_no_notices")
        return redirect(url_for("preview.settings_index"))

    r = rows[0]
    item = ParsedNotice(
        duid=r["duid"], title=r["title"],
        category_id=r["category_id"] if "category_id" in r.keys() else None,
        category_name=r["category_name"], author=r["author"],
        posted_date=r["posted_date"], modified_date=r["modified_date"],
        is_pinned=bool(r["is_pinned"]),
        has_attachment=bool(r["has_attachment"]),
        marked_as_new=False, url=r["url"],
    )

    channel = DiscordChannel(webhook)
    messages = channel._build_messages([item], [], datetime.now())
    ok = channel._post_all(messages)
    flash("success.test_send_ok" if ok else "error.test_send_failed")
    return redirect(url_for("preview.settings_index"))
