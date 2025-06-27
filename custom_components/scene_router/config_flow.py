"""Config flow for Scene Router integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import CONF_ENTRY_DEFAULT_NAME, DOMAIN


class SceneRouterConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for Scene Router integration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""

        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({}),
            )

        self.async_set_unique_id(DOMAIN)

        return self.async_create_entry(title=CONF_ENTRY_DEFAULT_NAME, data=user_input)
