"""Support for IINA Media Player as a Home Assistant receiver media_player entity."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.media_player import (
    BrowseMedia,
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
    async_process_play_media_url,
)
from homeassistant.components.media_player.const import (
    ATTR_MEDIA_ANNOUNCE,
    ATTR_MEDIA_ENQUEUE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ACTION_NEXT,
    ACTION_PAUSE,
    ACTION_PLAY,
    ACTION_PLAY_MEDIA,
    ACTION_PREV,
    ACTION_SEEK,
    ACTION_STOP,
    ACTION_TURN_OFF,
    ACTION_TURN_ON,
    ACTION_VOLUME_MUTE,
    ACTION_VOLUME_SET,
    ACTION_VOLUME_STEP,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    DOMAIN,
    STATE_BUFFERING,
    STATE_IDLE,
    STATE_OFF,
    STATE_PAUSED,
    STATE_PLAYING,
)
from .iina_client import IINAWebSocketClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the IINA media player entity."""
    client: IINAWebSocketClient = hass.data[DOMAIN][entry.entry_id]
    entity = IINAMediaPlayerEntity(client, entry)
    async_add_entities([entity], True)


class IINAMediaPlayerEntity(MediaPlayerEntity):
    """Representation of an IINA Media Player on macOS."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_device_class = MediaPlayerDeviceClass.RECEIVER

    def __init__(self, client: IINAWebSocketClient, entry: ConfigEntry) -> None:
        """Initialize the IINA media player."""
        self.client = client
        self.entry = entry
        self._attr_unique_id = entry.unique_id or f"iina_{entry.data[CONF_HOST]}_{entry.data[CONF_PORT]}"
        self._unsub_callback = None

        # Supported features
        self._attr_supported_features = (
            MediaPlayerEntityFeature.PLAY
            | MediaPlayerEntityFeature.PAUSE
            | MediaPlayerEntityFeature.STOP
            | MediaPlayerEntityFeature.VOLUME_SET
            | MediaPlayerEntityFeature.VOLUME_MUTE
            | MediaPlayerEntityFeature.VOLUME_STEP
            | MediaPlayerEntityFeature.SEEK
            | MediaPlayerEntityFeature.PLAY_MEDIA
            | MediaPlayerEntityFeature.PREVIOUS_TRACK
            | MediaPlayerEntityFeature.NEXT_TRACK
            | MediaPlayerEntityFeature.TURN_ON
            | MediaPlayerEntityFeature.TURN_OFF
            | MediaPlayerEntityFeature.MEDIA_ANNOUNCE
            | MediaPlayerEntityFeature.MEDIA_ENQUEUE
        )

    async def async_added_to_hass(self) -> None:
        """Register client callback when entity is added to Home Assistant."""
        self._unsub_callback = self.client.register_callback(self._handle_client_update)

    async def async_will_remove_from_hass(self) -> None:
        """Cleanup listener on removal."""
        if self._unsub_callback:
            self._unsub_callback()

    @callback
    def _handle_client_update(self) -> None:
        """Handle state updates from the IINA client."""
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return True if the IINA WebSocket client is connected."""
        return self.client.is_connected

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this IINA player."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            name=self.entry.title or self.client.hostname or "IINA Media Player",
            manufacturer="IINA",
            model="IINA Player macOS",
            sw_version="1.0.0",
        )

    @property
    def state(self) -> MediaPlayerState:
        """Return the current playback state."""
        if not self.client.is_connected:
            return MediaPlayerState.OFF

        iina_state = self.client.state
        if iina_state == STATE_PLAYING:
            return MediaPlayerState.PLAYING
        elif iina_state == STATE_PAUSED:
            return MediaPlayerState.PAUSED
        elif iina_state == STATE_BUFFERING:
            return MediaPlayerState.BUFFERING
        elif iina_state == STATE_OFF:
            return MediaPlayerState.OFF
        return MediaPlayerState.IDLE

    @property
    def volume_level(self) -> float | None:
        """Return the volume level from 0.0 to 1.0."""
        return max(0.0, min(1.0, self.client.volume_level / 100.0))

    @property
    def is_volume_muted(self) -> bool | None:
        """Return True if volume is muted."""
        return self.client.is_volume_muted

    @property
    def media_title(self) -> str | None:
        """Return the title of the currently playing media."""
        return self.client.media_title or None

    @property
    def media_artist(self) -> str | None:
        """Return the artist of the currently playing media."""
        return self.client.media_artist or None

    @property
    def media_album_name(self) -> str | None:
        """Return the album name of the currently playing media."""
        return self.client.media_album or None

    @property
    def media_duration(self) -> int | None:
        """Return the total duration of the media in seconds."""
        duration = self.client.media_duration
        return int(duration) if duration > 0 else None

    @property
    def media_position(self) -> int | None:
        """Return the current playback position in seconds."""
        position = self.client.media_position
        return int(position) if position >= 0 else None

    @property
    def media_position_updated_at(self):
        """Return the timestamp when the position was last updated."""
        return self.client.last_position_updated_at

    @property
    def media_image_url(self) -> str | None:
        """Return the cover image or thumbnail URL."""
        return self.client.media_image_url or None

    @property
    def media_content_type(self) -> MediaType:
        """Return the content type of current media."""
        return MediaType.MUSIC

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "playlist_position": self.client.playlist_pos,
            "playlist_count": self.client.playlist_count,
            "speed": self.client.speed,
            "url": self.client.current_url,
            "mac_host": self.client.hostname,
            "has_window": self.client.has_window,
        }

    async def async_media_play(self) -> None:
        """Send play command."""
        await self.client.send_command(ACTION_PLAY)

    async def async_media_pause(self) -> None:
        """Send pause command."""
        await self.client.send_command(ACTION_PAUSE)

    async def async_media_stop(self) -> None:
        """Send stop command."""
        await self.client.send_command(ACTION_STOP)

    async def async_media_seek(self, position: float) -> None:
        """Send seek command to absolute position."""
        await self.client.send_command(ACTION_SEEK, {"position": position})

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level (0.0 to 1.0)."""
        target_vol = int(round(volume * 100))
        await self.client.send_command(ACTION_VOLUME_SET, {"volume": target_vol})

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute / unmute volume."""
        await self.client.send_command(ACTION_VOLUME_MUTE, {"mute": mute})

    async def async_media_previous_track(self) -> None:
        """Send previous track command."""
        await self.client.send_command(ACTION_PREV)

    async def async_media_next_track(self) -> None:
        """Send next track command."""
        await self.client.send_command(ACTION_NEXT)

    async def async_turn_off(self) -> None:
        """Turn off player (stops media and closes player window)."""
        await self.client.send_command(ACTION_TURN_OFF)

    async def async_turn_on(self) -> None:
        """Turn on player (resumes playback or brings player to ready state)."""
        await self.client.send_command(ACTION_TURN_ON)

    async def async_play_media(
        self, media_type: MediaType | str, media_id: str, **kwargs: Any
    ) -> None:
        """Play media from URL, YouTube, HA Media Browser, or TTS."""
        announce = kwargs.get(ATTR_MEDIA_ANNOUNCE, False)
        enqueue = kwargs.get(ATTR_MEDIA_ENQUEUE, "play")

        # Process Home Assistant media URLs (Radio, TTS, Local HA Media)
        media_url = async_process_play_media_url(self.hass, media_id)

        # Map enqueue mode (value is now a plain string)
        enqueue_str = enqueue if isinstance(enqueue, str) else "play"

        _LOGGER.debug(
            "Playing media on IINA: url=%s, enqueue=%s, announce=%s",
            media_url,
            enqueue_str,
            announce,
        )

        await self.client.send_command(
            ACTION_PLAY_MEDIA,
            {
                "url": media_url,
                "enqueue": enqueue_str,
                "announce": bool(announce),
            },
        )
