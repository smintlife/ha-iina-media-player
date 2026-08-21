"""Config flow for IINA Media Player integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_RECONNECT_INTERVAL,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_RECONNECT_INTERVAL,
    DOMAIN,
)
from .iina_client import IINAWebSocketClient

_LOGGER = logging.getLogger(__name__)


class IINAConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for IINA Media Player."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._discovered_info: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial user step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            name = user_input.get(CONF_NAME, DEFAULT_NAME).strip() or DEFAULT_NAME

            # Unique ID based on host and port
            unique_id = f"iina_{host}_{port}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            # Test connection
            session = async_get_clientsession(self.hass)
            client = IINAWebSocketClient(host=host, port=port, session=session)

            try:
                connected = await client.connect()
                if not connected:
                    errors["base"] = "cannot_connect"
                else:
                    if client.hostname:
                        name = client.hostname
                    await client.close()
                    return self.async_create_entry(
                        title=name,
                        data={
                            CONF_HOST: host,
                            CONF_PORT: port,
                            CONF_NAME: name,
                        },
                    )
            except Exception as err:
                _LOGGER.error("Failed to connect during setup: %s", err)
                errors["base"] = "cannot_connect"
            finally:
                await client.close()

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> FlowResult:
        """Handle Zeroconf discovery."""
        host = discovery_info.host
        port = discovery_info.port or DEFAULT_PORT
        hostname = discovery_info.name.split(".")[0] if discovery_info.name else f"IINA ({host})"

        unique_id = f"iina_{host}_{port}"
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured(updates={CONF_HOST: host, CONF_PORT: port})

        self._discovered_info = {
            CONF_HOST: host,
            CONF_PORT: port,
            CONF_NAME: hostname,
        }

        self.context["title_placeholders"] = {"name": hostname}
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle user confirmation of Zeroconf discovery."""
        if user_input is not None:
            return self.async_create_entry(
                title=self._discovered_info[CONF_NAME],
                data=self._discovered_info,
            )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={
                "name": self._discovered_info[CONF_NAME],
                "host": self._discovered_info[CONF_HOST],
                "port": str(self._discovered_info[CONF_PORT]),
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return IINAOptionsFlow(config_entry)


class IINAOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for IINA integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_RECONNECT_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_RECONNECT_INTERVAL, DEFAULT_RECONNECT_INTERVAL
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=2, max=120)),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
