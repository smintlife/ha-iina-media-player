# AGENTS.md — ha-iina-media-player (Home Assistant Custom Integration)

## What this repo is
A Home Assistant **custom integration** (`custom_components/iina_media_player/`) that represents
the IINA media player (macOS) as a `media_player` entity with `device_class: receiver`.
It talks to the IINA plugin over a **WebSocket** connection (`ws://<host>:<port>`).

- Repo root: `ha-iina-media-player/`
- Key files:
  - `custom_components/iina_media_player/iina_client.py` — WebSocket client (connect, send commands, receive state).
  - `custom_components/iina_media_player/media_player.py` — HA `MediaPlayerEntity` (state, attributes, service calls).
  - `custom_components/iina_media_player/const.py` — constants, action identifiers, state strings.

## How to run / test
- This is Python (Home Assistant). No build step. Copy `custom_components/iina_media_player/` into a
  HA `custom_components/` dir, then **restart Home Assistant** (the WS listener is created at setup,
  so a reload is not enough — a full restart is required for connection changes).
- Enable debug logging via `configuration.yaml`:
  ```yaml
  logger:
    default: info
    logs:
      custom_components.iina_media_player: debug
  ```
- The integration sends `WS SEND -> action=...` and logs every received frame with
  `WS RECV <- <json>`.

## IINA WebSocket protocol (shared contract with the plugin repo)
- Commands sent TO IINA: JSON `{ "id": <n>, "action": <action>, "params": {...} }`
  - actions: `play`, `pause`, `play_pause`, `stop`, `seek`, `volume_set`, `volume_mute`,
    `volume_step`, `next`, `prev`, `play_media`, `turn_off`, `turn_on`, `get_state`
  - `play_media` params: `{ "url": "...", "enqueue": "play"|"replace"|"add"|"next", "announce": bool }`
- Responses: `{ "id": <n>, "success": bool, "result": <any> }` (HA waits up to 5s, then treats as success).
- Push events (no id): `{ "event": "state_update", "data": { ...PlayerStateData... } }`
  - PlayerStateData fields: `state` (`playing`/`paused`/`idle`/`buffering`/`off`), `has_window`,
    `media_title`, `media_artist`, `media_album`, `media_duration`, `media_position`,
    `media_image_url`, `volume_level` (0-100), `is_volume_muted`, `url`, `playlist_pos`,
    `playlist_count`, `hostname`, `speed`.

## CRITICAL learnings from the debugging session (READ BEFORE TOUCHING)
1. **IINA's `ws.sendText` sends payloads as BINARY WebSocket frames**, not TEXT.
   The Python client MUST handle `aiohttp.WSMsgType.BINARY` and decode with
   `msg.data.decode("utf-8")`, otherwise HA never receives any response/state → entity stuck on `idle`.
2. State updates come ONLY as `event: "state_update"` pushes. HA reads `data.state`,
   `data.media_title`, etc. Do not rely on `get_state` response for live state.
3. `iina_client.py` previously referenced a non-existent variable `msg` in `_handle_message`
   (caused an exception before state was applied). Fixed by logging `json.dumps(data)`.

## Interaction with the plugin repo (`iina-plugin-homeassistant`)
- This integration is the **client**. The IINA plugin (separate repo) is the **server**.
- Port default `8989` (`DEFAULT_PORT` in `const.py` and `port` preference in the plugin).
- Pairing tip: if HA shows no state / timeouts, confirm the plugin's WebSocket server is up
  (see plugin AGENTS.md "Address already in use" note) and that the plugin is actually loaded.
