# IINA Media Player Integration for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/AlexRoh/ha-iina-media-player)](https://github.com/AlexRoh/ha-iina-media-player/releases)

Eine vollwertige Home Assistant Custom Integration (`media_player` Entität mit `device_class: receiver`), um den Mediaplayer **IINA** auf macOS (Mac mini / MacBook / iMac) in Echtzeit per WebSocket fernzusteuern.

---

## ✨ Features

- **Receiver Device Class**: Integriert sich nahtlos als Receiver in Home Assistant Media-Karten und Dashboards.
- **Echtzeit-Zustandssynchronisation**: Push-Events für Status (`playing`, `paused`, `buffering`, `idle`, `off`), Track-Metadaten (Titel, Interpret, Album), Position, Gesamtlaufzeit und YouTube-Thumbnails.
- **Wiedergabesteuerung**: Play, Pause, Stop, Seek (Vor-/Zurückspulen), Next Track, Previous Track.
- **Lautstärke**: Stufenlose Regelung (0–100%) und Mute/Unmute mit Wert-Wiederherstellung.
- **YouTube & Web-Streaming**: Übergabe von YouTube-Videos/Playlisten und direkten Web-Stream-URLs über `media_player.play_media`.
- **Home Assistant Media Browser**: Wiedergabe von lokalen Home Assistant Medien, Webradio (Radio Browser) und Spotify-Streams.
- **Queue / Enqueue Modi**: Unterstützt `play`, `replace`, `add` (an Playlist anhängen) und `next`.
- **TTS-Ducking & Resume**: Spielt Sprachausgaben (`announce: true`) ab und setzt die vorherige Musik automatisch an der exakten Position fort.
- **Auto-Discovery (Zeroconf / Bonjour)**: Erkennt den Mac mini im lokalen Netzwerk automatisch für 1-Klick-Setup.
- **Automatische Wiederverbindung**: 3 sofortige Reconnect-Versuche bei Verbindungsverlust, gefolgt von periodischem Hintergrund-Reconnect.

---

## 📥 Installation

### Option 1: Über HACS (Empfohlen)
1. Öffnen Sie **HACS** in Home Assistant.
2. Gehen Sie auf **Integrationen** -> Menü oben rechts -> **Benutzerdefinierte Repositories**.
3. Fügen Sie die Repository-URL hinzu:
   - URL: `https://github.com/AlexRoh/ha-iina-media-player`
   - Kategorie: `Integration`
4. Suchen Sie nach **IINA Media Player** und klicken Sie auf **Herunterladen**.
5. Starten Sie Home Assistant neu.

### Option 2: Manuelle Installation
1. Kopieren Sie den Ordner `custom_components/iina_media_player` in das Verzeichnis `<config>/custom_components/` Ihrer Home Assistant Instanz.
2. Starten Sie Home Assistant neu.

---

## ⚙️ Konfiguration

1. Stellen Sie sicher, dass das **IINA Plugin (Home Assistant Bridge)** auf Ihrem Mac in IINA installiert und aktiv ist.
2. Gehen Sie in Home Assistant zu **Einstellungen -> Geräte & Dienste -> Integration hinzufügen**.
3. Suchen Sie nach **IINA Media Player** (oder bestätigen Sie die automatische Benachrichtigung via Zeroconf Auto-Discovery).
4. Geben Sie die IP-Adresse / Hostname des Mac mini und den Port (Standard: `8989`) ein.

---

## 💡 Anwendungsbeispiele & Automatisierungen

### 1. YouTube Musik / Video abspielen
```yaml
action: media_player.play_media
target:
  entity_id: media_player.iina_media_player
data:
  media_content_type: music
  media_content_id: "https://www.youtube.com/watch?v=5qap5aO4i9A"
```

### 2. Webradio Stream abspielen
```yaml
action: media_player.play_media
target:
  entity_id: media_player.iina_media_player
data:
  media_content_type: music
  media_content_id: "http://stream.srg-ssr.ch/m/rsj/mp3_128"
```

### 3. TTS-Durchsage mit automatischer Fortsetzung der Musik (Ducking)
```yaml
action: media_player.play_media
target:
  entity_id: media_player.iina_media_player
data:
  media_content_type: music
  media_content_id: "http://homeassistant.local:8123/api/tts_proxy/message.mp3"
  announce: true
```

### 4. Titel an Playlist anhängen (`enqueue: add`)
```yaml
action: media_player.play_media
target:
  entity_id: media_player.iina_media_player
data:
  media_content_type: music
  media_content_id: "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  enqueue: add
```
