"""Asynchronous WebSocket client for communication with the IINA Home Assistant plugin."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Callable

import aiohttp

_LOGGER = logging.getLogger(__name__)


class IINAWebSocketClient:
    """Client for controlling IINA via its WebSocket API."""

    def __init__(
        self,
        host: str,
        port: int,
        session: aiohttp.ClientSession | None = None,
        reconnect_interval: int = 10,
    ) -> None:
        """Initialize the IINA client."""
        self.host = host
        self.port = port
        self.url = f"ws://{host}:{port}"
        self._session = session
        self._owns_session = session is None
        self._reconnect_interval = reconnect_interval

        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._listen_task: asyncio.Task | None = None
        self._reconnect_task: asyncio.Task | None = None
        self._is_closing = False
        self._connected = False
        self._callbacks: list[Callable[[], None]] = []
        self._pending_requests: dict[int, asyncio.Future[dict[str, Any]]] = {}
        self._request_counter = 0

        # Cached player state
        self.state: str = "idle"
        self.has_window: bool = False
        self.media_title: str = ""
        self.media_artist: str = ""
        self.media_album: str = ""
        self.media_duration: float = 0.0
        self.media_position: float = 0.0
        self.media_image_url: str = ""
        self.volume_level: int = 100
        self.is_volume_muted: bool = False
        self.current_url: str = ""
        self.playlist_pos: int = 0
        self.playlist_count: int = 0
        self.hostname: str = ""
        self.speed: float = 1.0
        self.last_position_updated_at: datetime | None = None

    @property
    def is_connected(self) -> bool:
        """Return True if WebSocket is connected."""
        return self._connected and self._ws is not None and not self._ws.closed

    def register_callback(self, callback: Callable[[], None]) -> Callable[[], None]:
        """Register a callback for state changes."""
        self._callbacks.append(callback)

        def unsubscribe() -> None:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

        return unsubscribe

    def _notify_callbacks(self) -> None:
        """Notify all registered listeners about a state change."""
        for callback in self._callbacks:
            try:
                callback()
            except Exception as err:
                _LOGGER.error("Error in IINA client callback: %s", err)

    async def connect(self) -> bool:
        """Connect to the IINA WebSocket server with 3 initial retries."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._owns_session = True

        self._is_closing = False
        retry_count = 0
        max_initial_retries = 3

        while retry_count < max_initial_retries and not self._is_closing:
            try:
                _LOGGER.debug("Connecting to IINA WebSocket at %s (Attempt %d/%d)", self.url, retry_count + 1, max_initial_retries)
                self._ws = await self._session.ws_connect(self.url, timeout=aiohttp.ClientTimeout(total=5))
                self._connected = True
                _LOGGER.info("Connected to IINA WebSocket at %s", self.url)

                # Start listener task
                self._listen_task = asyncio.create_task(self._listen_loop())
                
                # Fetch initial state
                await self.send_command("get_state")
                self._notify_callbacks()
                return True
            except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as err:
                retry_count += 1
                _LOGGER.debug("Failed to connect to IINA (attempt %d/%d): %s", retry_count, max_initial_retries, err)
                if retry_count < max_initial_retries:
                    await asyncio.sleep(1.0)

        # If initial 3 attempts failed, start background reconnect task
        _LOGGER.warning("Could not connect to IINA at %s after %d attempts. Will retry in background.", self.url, max_initial_retries)
        self._connected = False
        self._notify_callbacks()
        self._start_reconnect_loop()
        return False

    def _start_reconnect_loop(self) -> None:
        """Start the background reconnect loop if not already running."""
        if self._reconnect_task is None or self._reconnect_task.done():
            self._reconnect_task = asyncio.create_task(self._reconnect_loop())

    async def _reconnect_loop(self) -> None:
        """Loop to reconnect to IINA in the background."""
        while not self._is_closing and not self.is_connected:
            try:
                await asyncio.sleep(self._reconnect_interval)
                if self._is_closing:
                    break
                _LOGGER.debug("Attempting to reconnect to IINA at %s...", self.url)
                if self._session is None or self._session.closed:
                    self._session = aiohttp.ClientSession()
                    self._owns_session = True

                self._ws = await self._session.ws_connect(self.url, timeout=aiohttp.ClientTimeout(total=5))
                self._connected = True
                _LOGGER.info("Reconnected successfully to IINA at %s", self.url)

                self._listen_task = asyncio.create_task(self._listen_loop())
                await self.send_command("get_state")
                self._notify_callbacks()
                break
            except Exception as err:
                _LOGGER.debug("Background reconnect to IINA failed: %s. Retrying in %ds...", err, self._reconnect_interval)
                self._connected = False
                self._notify_callbacks()

    async def _listen_loop(self) -> None:
        """Listen for incoming WebSocket messages."""
        if self._ws is None:
            return

        try:
            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        self._handle_message(data)
                    except json.JSONDecodeError as err:
                        _LOGGER.warning("Received invalid JSON from IINA: %s (%s)", msg.data, err)
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR, aiohttp.WSMsgType.CLOSING):
                    _LOGGER.info("WebSocket connection closed or received error")
                    break
        except Exception as err:
            _LOGGER.warning("Exception in WebSocket listener loop: %s", err)
        finally:
            self._connected = False
            self._notify_callbacks()
            if not self._is_closing:
                _LOGGER.info("Connection lost to IINA. Triggering reconnect loop.")
                self._start_reconnect_loop()

    def _handle_message(self, data: dict[str, Any]) -> None:
        """Handle parsed JSON message from IINA."""
        # Handle command responses
        req_id = data.get("id")
        if req_id is not None and req_id in self._pending_requests:
            future = self._pending_requests.pop(req_id)
            if not future.done():
                future.set_result(data)

        # Handle state updates (push events or result payloads)
        event_type = data.get("event")
        _LOGGER.info("WS RECV <- %s", msg.data if isinstance(msg.data, str) else "<binary>")
        if event_type == "state_update" and "data" in data:
            self._update_state_from_dict(data["data"])
            self._notify_callbacks()
        elif "result" in data and isinstance(data["result"], dict) and "state" in data["result"]:
            self._update_state_from_dict(data["result"])
            self._notify_callbacks()

    def _update_state_from_dict(self, state_dict: dict[str, Any]) -> None:
        """Update internal attributes from player state dictionary."""
        self.state = state_dict.get("state", "idle")
        self.has_window = bool(state_dict.get("has_window", False))
        self.media_title = state_dict.get("media_title", "")
        self.media_artist = state_dict.get("media_artist", "")
        self.media_album = state_dict.get("media_album", "")
        self.media_duration = float(state_dict.get("media_duration", 0.0))
        self.media_position = float(state_dict.get("media_position", 0.0))
        self.media_image_url = state_dict.get("media_image_url", "")
        self.volume_level = int(state_dict.get("volume_level", 100))
        self.is_volume_muted = bool(state_dict.get("is_volume_muted", False))
        self.current_url = state_dict.get("url", "")
        self.playlist_pos = int(state_dict.get("playlist_pos", 0))
        self.playlist_count = int(state_dict.get("playlist_count", 0))
        self.hostname = state_dict.get("hostname", self.hostname or self.host)
        self.speed = float(state_dict.get("speed", 1.0))
        self.last_position_updated_at = datetime.now(timezone.utc)

    async def send_command(self, action: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send a command over WebSocket to IINA."""
        if not self.is_connected or self._ws is None:
            _LOGGER.warning("Cannot send command '%s': WebSocket not connected", action)
            raise ConnectionError(f"IINA player at {self.url} is not connected")

        self._request_counter += 1
        req_id = self._request_counter
        message: dict[str, Any] = {
            "id": req_id,
            "action": action,
            "params": params or {},
        }

        loop = asyncio.get_running_loop()
        future: asyncio.Future[dict[str, Any]] = loop.create_future()
        self._pending_requests[req_id] = future

        try:
            await self._ws.send_str(json.dumps(message))
            _LOGGER.info(
                "WS SEND -> action=%s id=%d params=%s", action, req_id, params
            )
            # Wait up to 5 seconds for response
            return await asyncio.wait_for(future, timeout=5.0)
        except asyncio.TimeoutError:
            self._pending_requests.pop(req_id, None)
            _LOGGER.debug("Timed out waiting for response to '%s' (id=%d)", action, req_id)
            return {"id": req_id, "success": True}
        except Exception as err:
            self._pending_requests.pop(req_id, None)
            _LOGGER.error("Error sending command '%s' to IINA: %s", action, err)
            raise

    async def close(self) -> None:
        """Close the WebSocket connection and cleanup resources."""
        self._is_closing = True
        self._connected = False

        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()

        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()

        for future in self._pending_requests.values():
            if not future.done():
                future.cancel()
        self._pending_requests.clear()

        if self._ws and not self._ws.closed:
            await self._ws.close()

        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()

        self._notify_callbacks()
        _LOGGER.debug("IINA WebSocket client closed.")
