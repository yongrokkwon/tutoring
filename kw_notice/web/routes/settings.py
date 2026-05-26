import re
import sqlite3
from datetime import datetime
from typing import Optional

from flask import Blueprint, Response, flash, redirect, render_template, request, url_for

from ... import config, db
from ...crawler.parser import ParsedNotice
from ...notifier.discord import DiscordChannel
from ...repository import notices as notices_repo
from ...repository import settings as settings_repo
from ...repository import users as users_repo

bp = Blueprint("settings", __name__)

# seeds.sql 의 frequency_modes.(id, name) 와 동기 필요 — _pre-impl-checklist §1.4
FREQUENCY_NAME_TO_ID = {
    "custom": 0,
    "high":   1,
    "medium": 2,
    "low":    3,
}
FREQUENCY_ID_TO_NAME = {v: k for k, v in FREQUENCY_NAME_TO_ID.items()}
GRID_INTERVAL_MIN = 15

ERROR_MESSAGES = {
    "error.invalid_frequency_mode": "주기 모드 값이 올바르지 않습니다.",
    "error.no_time_selected":       "시각을 1개 이상 선택해주세요.",
    "error.invalid_time_format":    "시각 형식이 올바르지 않습니다.",
    "error.time_out_of_range":      "운영시간(10:00~17:00) 내 시각만 등록할 수 있습니다.",
    "error.time_not_aligned":       "15분 단위로만 등록할 수 있습니다.",
    "error.time_duplicated":        "이미 등록된 시각이 포함되어 있습니다.",
    "error.time_conflict":          "시각 등록 중 충돌이 발생했습니다. 다시 시도해주세요.",
    "error.test_send_no_webhook":   "Discord 웹훅 URL 이 설정되어 있지 않습니다.",
    "error.test_send_no_notices":   "보낼 공지가 없습니다. 먼저 크롤링이 동작했는지 확인하세요.",
    "error.test_send_failed":       "발송 테스트 실패 — Discord 웹훅 응답 오류. 로그 확인 필요.",
    "success.test_send_ok":         "발송 테스트 성공 — Discord 채널을 확인해주세요.",
}

_TIME_RE = re.compile(r"^\d{2}:\d{2}$")


@bp.get("/settings")
def index() -> str:
    with db.transaction() as conn:
        settings = settings_repo.load(conn)
        custom_times = settings_repo.list_custom_times_with_id(
            conn, config.DEFAULT_USER_ID)
    return render_template(
        "settings/index.html",
        settings=settings,
        custom_times=custom_times,
        frequency_id_to_name=FREQUENCY_ID_TO_NAME,
        error_messages=ERROR_MESSAGES,
    )


@bp.post("/settings")
def save() -> Response:
    mode_id = _parse_frequency_mode(request.form)
    is_active = _parse_is_active(request.form)
    if mode_id is None:
        flash("error.invalid_frequency_mode")
        return redirect(url_for("settings.index"))
    with db.transaction() as conn:
        settings_repo.update(conn, config.DEFAULT_USER_ID, mode_id, is_active)
    return redirect(url_for("settings.index"))


@bp.get("/settings/times/add")
def times_add_grid() -> str:
    with db.transaction() as conn:
        settings = settings_repo.load(conn)
    return render_template(
        "settings/times_add.html",
        grid=_grid_times(),
        registered=set(settings.custom_times),
        error_messages=ERROR_MESSAGES,
    )


@bp.post("/settings/times/add")
def times_add_save() -> Response:
    candidates = _parse_selected_times(request.form)
    if not candidates:
        flash("error.no_time_selected")
        return redirect(url_for("settings.times_add_grid"))
    with db.transaction() as conn:
        settings = settings_repo.load(conn)
        existing = set(settings.custom_times)
        valid, err = _validate_times(candidates, existing)
        if err is not None:
            flash(err)
            return redirect(url_for("settings.times_add_grid"))
        try:
            settings_repo.add_custom_times(
                conn, config.DEFAULT_USER_ID, valid or [])
        except sqlite3.IntegrityError:
            flash("error.time_conflict")
            return redirect(url_for("settings.times_add_grid"))
    return redirect(url_for("settings.index"))


@bp.post("/settings/times/delete")
def times_delete() -> Response:
    try:
        cid = int(request.form["id"])
    except (KeyError, ValueError):
        return redirect(url_for("settings.index"))
    with db.transaction() as conn:
        settings_repo.delete_custom_time(conn, config.DEFAULT_USER_ID, cid)
    return redirect(url_for("settings.index"))


@bp.post("/settings/test-send")
def test_send() -> Response:
    """area-4 §3.6 — 운영시간·is_active 무관 즉시 발송. service.send 비경유."""
    with db.transaction() as conn:
        webhook = users_repo.get_discord_webhook(conn, config.DEFAULT_USER_ID)
        if webhook is None:
            flash("error.test_send_no_webhook")
            return redirect(url_for("settings.index"))
        rows = notices_repo.list_recent(conn, limit=1)
    if not rows:
        flash("error.test_send_no_notices")
        return redirect(url_for("settings.index"))

    r = rows[0]
    item = ParsedNotice(
        duid=r["duid"], title=r["title"], category_id=r["category_id"]
            if "category_id" in r.keys() else None,
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
    return redirect(url_for("settings.index"))


def _parse_frequency_mode(form) -> Optional[int]:
    name = form.get("frequency_mode")
    return FREQUENCY_NAME_TO_ID.get(name)


def _parse_is_active(form) -> bool:
    return "is_active" in form


def _parse_selected_times(form) -> list[str]:
    return form.getlist("time")


def _validate_times(candidates: list[str],
                    existing: set[str]) -> tuple[Optional[list[str]], Optional[str]]:
    seen: set[str] = set()
    for t in candidates:
        if not _TIME_RE.match(t):
            return None, "error.invalid_time_format"
        hh, mm = int(t[:2]), int(t[3:])
        if not (config.OPERATING_HOUR_START * 60 <= hh * 60 + mm
                <= config.OPERATING_HOUR_END * 60):
            return None, "error.time_out_of_range"
        if mm % GRID_INTERVAL_MIN != 0:
            return None, "error.time_not_aligned"
        if t in existing or t in seen:
            return None, "error.time_duplicated"
        seen.add(t)
    return sorted(seen), None


def _grid_times() -> list[str]:
    times: list[str] = []
    for h in range(config.OPERATING_HOUR_START, config.OPERATING_HOUR_END):
        for m in (0, 15, 30, 45):
            times.append(f"{h:02d}:{m:02d}")
    times.append(f"{config.OPERATING_HOUR_END:02d}:00")
    return times
