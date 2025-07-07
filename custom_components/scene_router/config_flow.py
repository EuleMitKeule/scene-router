"""Config flow for Scene Router integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import voluptuous as vol

from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.components.scene import DOMAIN as SCENE_DOMAIN
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    CONF_CONDITIONS,
    CONF_ENABLE_AUTO_CHANGE,
    CONF_ERROR_CONDITION_REQUIRED,
    CONF_ERROR_NO_LIGHT_ENTITIES,
    CONF_ERROR_NO_SCENE_CONFIGS,
    CONF_ERROR_SCENE_REQUIRED,
    CONF_FORCING_CUSTOM_CONDITION,
    CONF_LIGHT_ENTITIES,
    CONF_NAME,
    CONF_REQUIRED_CUSTOM_CONDITION,
    CONF_SCENE,
    CONF_SCENE_CONFIGS,
    DEFAULT_ENABLE_AUTO_CHANGE,
    DOMAIN,
    SIGNAL_ENTRY_UPDATED,
    ConditionType,
)
from .models import SceneRouterConfig

_LOGGER = logging.getLogger(__name__)


def _get_schema(
    user_input: dict[str, Any] | None = None,
) -> vol.Schema:
    """Return the schema for the config flow."""
    if user_input is None:
        user_input = {}
    return vol.Schema(
        {
            vol.Required(
                CONF_NAME,
                description={
                    "suggested_value": user_input.get(CONF_NAME, ""),
                },
            ): str,
            vol.Required(
                CONF_ENABLE_AUTO_CHANGE,
                description={
                    "suggested_value": user_input.get(
                        CONF_ENABLE_AUTO_CHANGE, DEFAULT_ENABLE_AUTO_CHANGE
                    ),
                },
            ): bool,
            vol.Required(
                CONF_LIGHT_ENTITIES,
                description={
                    "suggested_value": user_input.get(CONF_LIGHT_ENTITIES, []),
                },
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain=LIGHT_DOMAIN,
                    multiple=True,
                )
            ),
            vol.Optional(
                CONF_SCENE_CONFIGS,
                description={
                    "suggested_value": user_input.get(CONF_SCENE_CONFIGS, []),
                },
            ): selector.selector(
                {
                    "object": {
                        "fields": {
                            CONF_SCENE: {
                                "label": CONF_SCENE,
                                "required": True,
                                "selector": {
                                    "entity": {
                                        "domain": SCENE_DOMAIN,
                                        "multiple": False,
                                    }
                                },
                            },
                            CONF_CONDITIONS: {
                                "label": CONF_CONDITIONS,
                                "required": False,
                                "selector": {
                                    "select": {
                                        "options": [
                                            {
                                                "value": condition_type.value,
                                                "label": condition_type.value,
                                            }
                                            for condition_type in ConditionType
                                        ],
                                        "multiple": True,
                                        "mode": "dropdown",
                                        "translation_key": CONF_CONDITIONS,
                                        "sort": True,
                                    },
                                },
                            },
                            CONF_REQUIRED_CUSTOM_CONDITION: {
                                "label": CONF_REQUIRED_CUSTOM_CONDITION,
                                "required": False,
                                "selector": {"condition": {"multiple": True}},
                            },
                            CONF_FORCING_CUSTOM_CONDITION: {
                                "label": CONF_FORCING_CUSTOM_CONDITION,
                                "required": False,
                                "selector": {"condition": {"multiple": True}},
                            },
                        },
                        "label_field": CONF_SCENE,
                        "description_field": CONF_CONDITIONS,
                        "read_only": False,
                        "multiple": True,
                        "translation_key": CONF_SCENE_CONFIGS,
                    }
                }
            ),
        }
    )


def _get_errors(user_input: dict[str, Any]) -> dict[str, str]:
    """Return a dictionary of errors based on user input."""
    errors: dict[str, str] = {}

    if not user_input.get(CONF_LIGHT_ENTITIES):
        errors[CONF_LIGHT_ENTITIES] = CONF_ERROR_NO_LIGHT_ENTITIES

    if not user_input.get(CONF_SCENE_CONFIGS):
        errors[CONF_SCENE_CONFIGS] = CONF_ERROR_NO_SCENE_CONFIGS

    for scene_config in user_input.get(CONF_SCENE_CONFIGS, []):
        if TYPE_CHECKING:
            assert isinstance(scene_config, dict)

        if not scene_config.get(CONF_SCENE):
            errors[CONF_SCENE_CONFIGS] = CONF_ERROR_SCENE_REQUIRED
        if not scene_config.get(CONF_CONDITIONS) and not scene_config.get(
            CONF_FORCING_CUSTOM_CONDITION
        ):
            errors[CONF_SCENE_CONFIGS] = CONF_ERROR_CONDITION_REQUIRED

    return errors


class SceneRouterConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for Scene Router integration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""

        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=_get_schema())

        _LOGGER.debug(
            "Creating Scene Router configuration with user input: %s", user_input
        )

        errors = _get_errors(user_input)
        if errors:
            return self.async_show_form(
                step_id="user",
                data_schema=_get_schema(user_input),
                errors=errors,
            )

        return self.async_create_entry(
            title=user_input[CONF_NAME], data={}, options=user_input
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(dict(config_entry.options))


class OptionsFlowHandler(OptionsFlow):
    """Handle Options flow for Scene Router."""

    def __init__(self, options: dict[str, Any]) -> None:
        """Initialize the options flow handler."""
        self.options = options

    async def async_step_init(self, user_input=None):
        """Handle initial step."""

        if user_input is None:
            return self.async_show_form(
                step_id="init",
                data_schema=_get_schema(self.options),
            )

        _LOGGER.debug(
            "Updating Scene Router configuration with user input: %s",
            user_input,
        )

        errors = _get_errors(user_input)
        if errors:
            return self.async_show_form(
                step_id="init",
                data_schema=_get_schema(self.options),
                errors=errors,
            )

        previous_options = SceneRouterConfig.from_dict(self.options)
        new_options = SceneRouterConfig.from_dict(user_input)

        async_dispatcher_send(
            self.hass,
            f"{DOMAIN}_{self.config_entry.entry_id}_{SIGNAL_ENTRY_UPDATED}",
            previous_options,
            new_options,
        )

        return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)
