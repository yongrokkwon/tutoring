from flask import Blueprint, redirect, render_template, url_for

from ... import db
from ...repository import notices as notices_repo

bp = Blueprint("notices", __name__)


@bp.get("/")
def root():
    return redirect(url_for("notices.index"))


@bp.get("/notices")
def index() -> str:
    with db.transaction() as conn:
        rows = notices_repo.list_recent(conn, limit=100)
    return render_template("notices/index.html", notices=rows)
