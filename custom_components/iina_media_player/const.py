"""Constants for the IINA Media Player integration."""

DOMAIN = "iina_media_player"
DEFAULT_NAME = "IINA Media Player"
DEFAULT_PORT = 8989

CONF_HOST = "host"
CONF_PORT = "port"
CONF_NAME = "name"
CONF_RECONNECT_INTERVAL = "reconnect_interval"

DEFAULT_RECONNECT_INTERVAL = 10  # seconds

# Action identifiers
ACTION_PLAY = "play"
ACTION_PAUSE = "pause"
ACTION_PLAY_PAUSE = "play_pause"
ACTION_STOP = "stop"
ACTION_SEEK = "seek"
ACTION_VOLUME_SET = "volume_set"
ACTION_VOLUME_MUTE = "volume_mute"
ACTION_VOLUME_STEP = "volume_step"
ACTION_NEXT = "next"
ACTION_PREV = "prev"
ACTION_PLAY_MEDIA = "play_media"
ACTION_TURN_OFF = "turn_off"
ACTION_TURN_ON = "turn_on"
ACTION_GET_STATE = "get_state"

# Player state strings from IINA
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_IDLE = "idle"
STATE_BUFFERING = "buffering"
STATE_OFF = "off"
