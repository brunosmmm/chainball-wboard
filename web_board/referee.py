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
from typing import Set

from flask_login import login_user, logout_user, login_required, login_fresh

from web_board import LOGIN_MANAGER
from web_board.ipc import ScoreboardIPCClient as ipc
from web_board.ipc import ScoreboardIPCError, ScoreboardIPCTimeoutError
from web_board.utils import LoginForm, is_safe_url

bp = Blueprint("referee", __name__)


class WebIPCCallRegistry:
    """Registry of IPC functions."""

    FN_NAMES: Set[str] = set()

    def __init__(self, function):
        """Initialize."""
        WebIPCCallRegistry.FN_NAMES |= set(["referee." + function.__name__])

    def __call__(self, function):
        """Call."""
        return function


def web_ipc_call(**deco_kwargs):
    """Web API decorator to write less."""

    def wrapper(func):
        @functools.wraps(func)
        @login_required
        @WebIPCCallRegistry(func)
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
            except ScoreboardIPCError:
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


@bp.route("/")
@login_required
async def referee_index():
    """Referee panel."""
    preg = asyncio.ensure_future(ipc.retrieve_registry(registry_id="player"))
    greg = asyncio.ensure_future(ipc.retrieve_registry(registry_id="game"))
    treg = asyncio.ensure_future(
        ipc.retrieve_registry(registry_id="tournament")
    )
    gamestatus = asyncio.ensure_future(ipc.game_status())
    playerstatus = asyncio.ensure_future(ipc.player_status())

    ret = await asyncio.gather(
        preg, greg, treg, gamestatus, playerstatus, return_exceptions=True
    )

    ipc_error = False
    for item in ret:
        if isinstance(item, Exception):
            ipc_error = True
            pregistry = []
            gregistry = []
            tregistry = []
            gstatus = {}
            pstatus = {}
            break

    if ipc_error is False:
        pregistry, gregistry, tregistry, gstatus, pstatus = ret
        pregistry = {player["username"]: player for player in pregistry}
        gregistry = {game["identifier"]: game for game in gregistry}
        tregistry = {tournament["id"]: tournament for tournament in tregistry}

    return await render_template(
        "referee.html",
        pregistry=pregistry,
        gregistry=gregistry,
        tregistry=tregistry,
        gstatus=gstatus,
        pstatus=pstatus,
        registered_players=[player["username"] for player in pstatus.values()],
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


@bp.route("/control/activateTournament/<tid>")
@login_required
async def activate_tournament(tid):
    """Activate tournament."""
    try:
        await ipc.activate_tournament(tournament_id=tid)
        data = {"status": "ok"}
    except ScoreboardIPCError:
        data = {"status": "error"}

    return jsonify(data)


@bp.route("/control/deactivateTournament")
@web_ipc_call()
async def deactivate_tournament(data):
    """Deactivate tournament."""


@bp.route("/control/activateGame/<gid>")
@login_required
async def activate_game(gid):
    """Activate game."""
    try:
        await ipc.activate_game(game_id=int(gid))
        data = {"status": "ok"}
    except ScoreboardIPCError:
        data = {"status": "error"}
    except ValueError:
        data = {"status": "error", "error": "invalid game id"}

    return jsonify(data)


@bp.route("/control/pregister/<pnum>,<pid>", methods=["GET"])
@login_required
async def register_player(pnum, pid):
    """Register player."""
    # perform minimal checking
    try:
        player_num = int(pnum)
        if player_num < 0 or player_num > 3:
            raise ValueError
    except ValueError:
        return jsonify({"status": "error", "error": "invalid player number"})

    try:
        await ipc.player_register(username=pid, player_num=player_num)
        data = {"status": "ok"}
    except ScoreboardIPCError:
        data = {"status": "error"}

    return jsonify(data)


@bp.route("/control/punregister/<pnum>")
@login_required
async def unregister_player(pnum):
    """Unregister player."""
    try:
        player_num = int(pnum)
        if player_num < 0 or player_num > 3:
            raise ValueError
    except ValueError:
        return jsonify({"status": "error", "error": "invalid player number"})

    try:
        await ipc.player_unregister(player_number=player_num)
        data = {"status": "ok"}
    except ScoreboardIPCError:
        data = {"status": "error"}

    return jsonify(data)


@bp.route("/login", methods=["GET", "POST"])
async def login():
    """Log in."""
    currently_authenticated = (
        current_app.user_class.get_currently_authenticated()
    )
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

            return redirect(_next or url_for("referee.referee_index"))
        await flash("Log in failed!")
    return await render_template("login.html", form=form)


@bp.route("/control/event/<pnum>,<evt>")
@login_required
async def event(pnum, evt):
    """Event."""
    try:
        player_num = int(pnum)
    except ValueError:
        return jsonify({"status": "error", "error": "invalid player id"})

    if player_num < 0 or player_num > 3:
        return jsonify({"status": "error", "error": "invalid player id"})

    try:
        await ipc.score_event(player_num=player_num, evt_type=evt)
        data = {"status": "ok"}
    except ScoreboardIPCError:
        data = {"status": "error"}
    return jsonify(data)


@bp.route("/control/setturn/<pnum>")
@login_required
async def set_turn(pnum):
    """Set turn manually."""

    try:
        player_num = int(pnum)
    except ValueError:
        return jsonify({"status": "error", "error": "invalid player id"})

    if player_num < 0 or player_num > 3:
        return jsonify({"status": "error", "error": "invalid player id"})

    try:
        await ipc.set_turn(player_num=player_num)
        data = {"status": "ok"}
    except ScoreboardIPCError:
        data = {"status": "error"}

    return jsonify(data)


@bp.route("/control/setscore/<pnum>,<score>")
@login_required
async def set_score(pnum, score):
    """Set score manually."""

    try:
        player_num = int(pnum)
        score = int(score)
    except ValueError:
        return jsonify(
            {"status": "error", "error": "invalid player id or score"}
        )

    if player_num < 0 or player_num > 3:
        return jsonify({"status": "error", "error": "invalid player id"})

    if score < -10 or score > 5:
        return jsonify({"status": "error", "error": "invalid score"})

    try:
        await ipc.set_score(player_num=player_num, score=score)
        data = {"status": "ok"}
    except ScoreboardIPCError:
        data = {"status": "error"}
    return jsonify(data)


@bp.route("/cbcentral/update")
@web_ipc_call()
async def update_registry(data):
    """Update registry"""


@bp.route("/logout")
@login_required
async def logout():
    """Log out."""
    username = current_app.user_class.get_currently_authenticated()
    user = current_app.user_class.get(username)
    user.is_authenticated = False
    logout_user()
    return redirect(url_for("referee.login"))


@LOGIN_MANAGER.unauthorized_handler
def unauthorized():
    """Handle unauthorized access."""
    # do stuff
    if request.endpoint in WebIPCCallRegistry.FN_NAMES:
        # IPC API call
        return jsonify({"status": "error", "error": "unauthorized access"})
    return redirect(url_for("referee.login"))
