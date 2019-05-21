"""Referee panel."""
from quart import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
    jsonify,
    current_app,
    flash,
    abort,
)


import asyncio
import functools

from flask_login import login_user, logout_user, login_required, login_fresh

from web_board.ipc import ScoreboardIPCClient as ipc
from web_board.ipc import ScoreboardIPCError, ScoreboardIPCTimeoutError
from web_board.utils import LoginForm, is_safe_url

bp = Blueprint("referee", __name__)


def web_ipc_call(**deco_kwargs):
    """Web API decorator to write less."""

    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            ipc_type = func.__name__
            try:
                data = await ipc.do_ipc_call(ipc_type, **deco_kwargs)
                if isinstance(data, dict):
                    data["status"] = "ok"
                elif data is not None:
                    data = {"status": "ok", "data": data}
                else:
                    data = {"status": "ok"}
            except (ScoreboardIPCError):
                data = {"status": "error", "error": "request error"}
            except ScoreboardIPCTimeoutError:
                data = {"status": "error", "error": "ipc timeout"}

            # call function on data
            ret = await func(data)
            if ret is None:
                ret = data

            return jsonify(ret)

        return wrapped

    return wrapper


@bp.route("/referee")
@login_required
async def referee_index():
    """Referee panel."""
    preg = asyncio.ensure_future(ipc.retrieve_registry(registry_id="player"))
    greg = asyncio.ensure_future(ipc.retrieve_registry(registry_id="game"))
    treg = asyncio.ensure_future(
        ipc.retrieve_registry(registry_id="tournament")
    )
    tid_get = asyncio.ensure_future(ipc.tournament_active())

    ret = await asyncio.gather(
        preg, greg, treg, tid_get, return_exceptions=True
    )

    ipc_error = False
    for item in ret:
        if isinstance(item, Exception):
            ipc_error = True
            pregistry = []
            gregistry = []
            tregistry = []
            tid = None
            break

    if ipc_error is False:
        pregistry, gregistry, tregistry, tid = ret

    return await render_template(
        "referee.html",
        pregistry=pregistry,
        gregistry=gregistry,
        tregistry=tregistry,
        tournament_id=str(tid),
        ipc_error=ipc_error,
    )


@bp.route("/status/game")
@web_ipc_call()
async def game_status(data):
    """Get game status."""


@bp.route("/status/players")
@web_ipc_call()
async def player_status(data):
    """Get player status."""


@bp.route("/status/can_start")
async def game_can_start():
    """Get whether can start."""
    try:
        data = {}
        data["can_start"] = await ipc.game_can_start()
        data["status"] = "ok"
    except ScoreboardIPCError:
        data = {"status": "error"}

    return jsonify(data)


@bp.route("/control/gbegin")
@web_ipc_call()
async def game_begin(data):
    """Start the game."""


@bp.route("/control/gend")
@web_ipc_call()
async def game_end(data):
    """End the game."""


@bp.route("/persist/tournament/<tid>")
async def activate_tournament(tid):
    """Activate tournament."""
    try:
        await ipc.activate_tournament(tournament_id=tid)
        data = {"status": "ok"}
    except ScoreboardIPCError:
        data = {"status": "error"}

    return jsonify(data)


@bp.route("/persist/tournament_off")
@web_ipc_call()
async def deactivate_tournament(data):
    """Deactivate tournament."""


@bp.route("/", methods=["GET", "POST"])
async def login():
    """Log in."""
    currently_authenticated = (
        current_app.user_class.get_currently_authenticated()
    )
    if currently_authenticated is not None and login_fresh():
        return redirect(url_for("referee.referee_index"))
    form = LoginForm()
    if form.validate_on_submit():
        # verify user
        if form.user_name.data == currently_authenticated:
            # deny
            return await abort(401)
        user = current_app.user_class.get(form.user_name.data)
        # verify password
        if user is not None and current_app.bcrypt.check_password_hash(
            user.password_hash, form.password.data
        ):
            # authenticate user
            user.is_authenticated = True
            login_user(user)

            await flash("Log in successful.")

            _next = request.args.get("next")
            if not is_safe_url(_next):
                return await abort(400)

            return redirect(_next or url_for("index"))
        await flash("Log in failed!")
    return await render_template("login.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    """Log out."""
    username = current_app.user_class.get_currently_authenticated()
    user = current_app.user_class.get(username)
    user.is_authenticated = False
    logout_user()
    return redirect(url_for("login"))
