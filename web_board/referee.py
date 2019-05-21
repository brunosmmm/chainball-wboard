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
)

import asyncio
import functools

from web_board.ipc import ScoreboardIPCClient as ipc
from web_board.ipc import ScoreboardIPCError

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
            except ScoreboardIPCError:
                data = {"status": "error"}

            # call function on data
            ret = await func(data)
            if ret is None:
                ret = data

            return jsonify(ret)

        return wrapped

    return wrapper


@bp.route("/")
async def index():
    """Referee panel."""
    preg = asyncio.ensure_future(ipc.retrieve_registry(registry_id="player"))
    greg = asyncio.ensure_future(ipc.retrieve_registry(registry_id="game"))
    treg = asyncio.ensure_future(
        ipc.retrieve_registry(registry_id="tournament")
    )
    tid_get = asyncio.ensure_future(ipc.tournament_active())

    pregistry, gregistry, tregistry, tid = await asyncio.gather(
        preg, greg, treg, tid_get, return_exceptions=True
    )
    return await render_template(
        "referee.html",
        pregistry=pregistry,
        gregistry=gregistry,
        tregistry=tregistry,
        tournament_id=str(tid),
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
