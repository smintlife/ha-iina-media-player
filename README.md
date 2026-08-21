# IINA Media Player Integration for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/AlexRoh/ha-iina-media-player)](https://github.com/AlexRoh/ha-iina-media-player/releases)

A full-featured Home Assistant Custom Integration (`media_player` entity with `device_class: receiver`) to remotely control the **IINA** media player on macOS (Mac mini / MacBook / iMac) in real time via WebSocket.

---

## ✨ Features

- **Receiver Device Class**: Seamlessly integrates as a receiver entity in Home Assistant media cards, dashboards, and media browsers.
- **Real-Time State Synchronization**: Push events for state (`playing`, `paused`, `buffering`, `idle`, `off`), track metadata (title, artist, album), position, duration, and YouTube thumbnails.
- **Playback Control**: Play, Pause, Stop, Seek (forward/backward), Next Track, Previous Track.
- **Volume & Mute**: Smooth volume control (0–100%) and Mute/Unmute with previous value restoration.
- **YouTube & Web Streaming**: Pass YouTube videos/playlists and direct web stream URLs via `media_player.play_media`.
- **Home Assistant Media Browser**: Play local Home Assistant media files, web radio (Radio Browser), and streaming services.
- **Queue / Enqueue Modes**: Full support for `play`, `replace`, `add` (append to playlist), and `next`.
- **TTS Ducking & Resume**: Automatically pauses current playback during TTS announcements (`announce: true`) and resumes at the exact saved position.
- **Auto-Discovery (Zeroconf / Bonjour)**: Discovers the Mac mini automatically on the local network for 1-click setup.
- **Automatic Reconnection**: 3 immediate reconnect attempts upon connection loss, followed by resilient periodic background reconnection.

---

## 📥 Installation

### Option 1: Via HACS (Recommended)
1. Open **HACS** in Home Assistant.
2. Go to **Integrations** -> top-right menu -> **Custom repositories**.
3. Add the repository URL:
   - URL: `https://github.com/AlexRoh/ha-iina-media-player`
   - Type: `Integration`
4. Search for **IINA Media Player** and click **Download**.
5. Restart Home Assistant.

### Option 2: Manual Installation
1. Copy the `custom_components/iina_media_player` directory into `<config>/custom_components/` in your Home Assistant configuration directory.
2. Restart Home Assistant.

---

## ⚙️ Configuration

1. Ensure the **IINA Plugin (Home Assistant Bridge)** is installed and enabled in IINA on your Mac.
2. In Home Assistant, navigate to **Settings -> Devices & Services -> Add Integration**.
3. Search for **IINA Media Player** (or click configure on the discovered Zeroconf notification).
4. Enter the host/IP address of the Mac mini and port (default: `8989`).

---

## 💡 Usage Examples & Automations

### 1. Play YouTube Music / Video
```yaml
action: media_player.play_media
target:
  entity_id: media_player.iina_media_player
data:
  media_content_type: music
  media_content_id: "https://www.youtube.com/watch?v=5qap5aO4i9A"
```

### 2. Play Web Radio Stream
```yaml
action: media_player.play_media
target:
  entity_id: media_player.iina_media_player
data:
  media_content_type: music
  media_content_id: "http://stream.srg-ssr.ch/m/rsj/mp3_128"
```

### 3. TTS Announcement with Automatic Music Resume (Ducking)
```yaml
action: media_player.play_media
target:
  entity_id: media_player.iina_media_player
data:
  media_content_type: music
  media_content_id: "http://homeassistant.local:8123/api/tts_proxy/message.mp3"
  announce: true
```

### 4. Append Song to Playlist (`enqueue: add`)
```yaml
action: media_player.play_media
target:
  entity_id: media_player.iina_media_player
data:
  media_content_type: music
  media_content_id: "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  enqueue: add
```
