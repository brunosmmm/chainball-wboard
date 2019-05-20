"""Referee panel."""
from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.exceptions import abort


bp = Blueprint("referee", __name__)


@bp.route("/")
def index():
    """Show all the posts, most recent first."""
    return render_template("referee.html", posts=posts)
