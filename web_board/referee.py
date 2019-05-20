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

from web_board.ipc import ScoreboardIPCClient as ipc
from web_board.ipc import ScoreboardIPCError

bp = Blueprint("referee", __name__)


@bp.route("/")
async def index():
    """Referee panel."""
    preg = asyncio.ensure_future(ipc.retrieve_registry(registry_id="player"))
    greg = asyncio.ensure_future(ipc.retrieve_registry(registry_id="game"))
    treg = asyncio.ensure_future(
        ipc.retrieve_registry(registry_id="tournament")
    )

    pregistry, gregistry, tregistry = await asyncio.gather(
        preg, greg, treg, return_exceptions=True
    )
    return await render_template(
        "referee.html",
        pregistry=pregistry,
        gregistry=gregistry,
        tregistry=tregistry,
    )


@bp.route("/status/game")
async def game_status():
    """Get game status."""
    try:
        data = await ipc.game_status()
        data["status"] = "ok"
    except ScoreboardIPCError:
        data = {"status": "error"}
    return jsonify(data)


@bp.route("/status/players")
async def player_status():
    """Get player status."""
    try:
        data = await ipc.player_status()
        data["status"] = "ok"
    except ScoreboardIPCError:
        data = {"status": "error"}
    return jsonify(data)


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
