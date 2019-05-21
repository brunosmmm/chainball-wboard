"""Scoreboard IPC client."""

from collections import deque
from typing import Deque, Optional

import asyncio
import functools
import zmq
import json
from zmq.asyncio import Context

EVENT_QUEUE: Deque = deque()


async def receive_events():
    """Receive events."""
    ctx = Context.instance()
    socket = ctx.socket(zmq.SUB)
    socket.connect("tcp://127.0.0.1:5556")
    socket.subscribe(b"")
    while True:
        msg = await socket.recv_multipart()
        EVENT_QUEUE.append(msg)
    socket.close()


class ScoreboardIPCError(Exception):
    """Error."""

    def __init__(self, message: str, data: Optional[str] = None):
        super().__init__(message)
        self._data = data

    @property
    def data(self):
        """Get error data."""
        return self._data


class ScoreboardIPCTimeoutError(Exception):
    """Timeout."""


async def _ipc_call(call_type: str, **kwargs):
    """Call IPC."""
    ctx = Context.instance()
    socket = ctx.socket(zmq.REQ)
    socket.setsockopt(zmq.RCVTIMEO, 100)
    socket.setsockopt(zmq.LINGER, 0)
    socket.connect("tcp://127.0.0.1:5555")
    # send request
    try:
        json_data = json.dumps((call_type, kwargs))
        await socket.send_multipart([json_data.encode()])
    except zmq.ZMQError:
        raise ScoreboardIPCError("could not call server")
    except zmq.error.Again:
        # timeout
        raise ScoreboardIPCTimeoutError("connection timed out")
    # get response
    try:
        recv_data = await socket.recv_multipart()
        status, data = json.loads(recv_data[0].decode())
    except zmq.ZMQError:
        raise ScoreboardIPCError("could not receive data from server")
    except (json.JSONDecodeError, TypeError):
        raise ScoreboardIPCError("received malformed response")
    except zmq.error.Again:
        raise ScoreboardIPCTimeoutError("connection timed out")
    socket.close()
    if status != "ok":
        raise ScoreboardIPCError("IPC error occurred", data)

    return data


def ipc_call():
    """IPC call.."""

    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(**kwargs):
            # Some fancy boo stuff
            data = await _ipc_call(func.__name__, **kwargs)
            ret = await func(data=data, **kwargs)
            if ret is None:
                return data

        return wrapped

    return wrapper


class ScoreboardIPCClient:
    """IPC Client."""

    @staticmethod
    async def do_ipc_call(call_type, **kwargs):
        """Call."""
        if not hasattr(ScoreboardIPCClient, call_type):
            raise ScoreboardIPCError("invalid call type: {}".format(call_type))
        function = getattr(ScoreboardIPCClient, call_type)
        return await function(**kwargs)

    @staticmethod
    @ipc_call()
    async def game_can_start(**kwargs):
        """Get whether game can be started."""

    @staticmethod
    @ipc_call()
    async def score_status(**kwargs):
        """Get score data."""

    @staticmethod
    @ipc_call()
    async def player_status(**kwargs):
        """Get player data."""

    @staticmethod
    @ipc_call()
    async def tournament_active(**kwargs):
        """Get tournament status."""

    @staticmethod
    @ipc_call()
    async def activate_tournament(tournament_id: int = 0, **kwargs):
        """Activate tournament."""

    @staticmethod
    @ipc_call()
    async def deactivate_tournament(**kwargs):
        """Deactivate tournament."""

    @staticmethod
    @ipc_call()
    async def update_registry(**kwargs):
        """Update registry."""

    @staticmethod
    @ipc_call()
    async def retrieve_registry(registry_id: str = "player", **kwargs):
        """Retrieve registry data."""

    @staticmethod
    @ipc_call()
    async def game_begin(**kwargs):
        """Start game."""

    @staticmethod
    @ipc_call()
    async def game_end(**kwargs):
        """Stop game."""

    @staticmethod
    @ipc_call()
    async def remote_pair(player_number: int = 0, **kwargs):
        """Pair remote."""

    @staticmethod
    @ipc_call()
    async def remote_unpair(player_number: int = 0, **kwargs):
        """Unpair remote."""

    @staticmethod
    @ipc_call()
    async def player_register(web_txt: str = "", panel_txt: str = "", **kwargs):
        """Register player."""

    @staticmethod
    @ipc_call()
    async def player_unregister(player_number: int = 0):
        """Unregister player."""

    @staticmethod
    @ipc_call()
    async def score_event(evt_type: str = "", player_num: int = 0, **kwargs):
        """Scoring event."""

    @staticmethod
    @ipc_call()
    async def set_turn(player_num: int = 0, **kwargs):
        """Set turn."""

    @staticmethod
    @ipc_call()
    async def set_score(player_num: int = 0, score: int = 0, **kwargs):
        """Set score."""

    @staticmethod
    @ipc_call()
    async def game_status(**kwargs):
        """Get game status."""
