"""Validation for the Scene Router YAML configuration."""

import voluptuous as vol

from homeassistant.helpers import config_validation as cv

from .const import DOMAIN

# ─── Condition-Schemas ────────────────────────────────────────────────────────

LUX_CONDITION_SCHEMA = vol.Schema(
    {
        vol.Optional("above"): vol.Coerce(float),
        vol.Optional("below"): vol.Coerce(float),
    },
    extra=vol.PREVENT_EXTRA,
)

ELEVATION_CONDITION_SCHEMA = vol.Schema(
    {
        vol.Optional("above"): vol.Coerce(float),
        vol.Optional("below"): vol.Coerce(float),
    },
    extra=vol.PREVENT_EXTRA,
)

TIME_CONDITION_SCHEMA = vol.Schema(
    {
        vol.Optional("after"): cv.time,
        vol.Optional("before"): cv.time,
    },
    extra=vol.PREVENT_EXTRA,
)

SCENE_SCHEMA = vol.Schema(
    {
        # Pflichtfeld: scene-Entity
        vol.Required("scene"): cv.entity_id,
        # Freie HA-Conditions
        vol.Optional("conditions", default=[]): cv.ensure_list,
        # Spezielle Conditions-Listen
        vol.Optional("lux_conditions", default=[]): vol.All(
            cv.ensure_list, [LUX_CONDITION_SCHEMA]
        ),
        vol.Optional("elevation_conditions", default=[]): vol.All(
            cv.ensure_list, [ELEVATION_CONDITION_SCHEMA]
        ),
        vol.Optional("time_conditions", default=[]): vol.All(
            cv.ensure_list, [TIME_CONDITION_SCHEMA]
        ),
    },
    extra=vol.PREVENT_EXTRA,
)

# ─── Router-Entry Schema ───────────────────────────────────────────────────────

ROUTER_SCHEMA = vol.Schema(
    {
        vol.Required("name"): cv.string,
        vol.Optional("enable_device", default=True): cv.boolean,
        vol.Optional("enable_preview_sensor", default=True): cv.boolean,
        vol.Optional("enable_auto_change", default=True): cv.boolean,
        vol.Optional("enable_condition_entities", default=True): cv.boolean,
        vol.Required("lights"): vol.All(cv.ensure_list, [cv.entity_id]),
        vol.Optional("lux_sensors", default=[]): vol.All(
            cv.ensure_list, [cv.entity_id]
        ),
        vol.Required("scenes"): vol.All(cv.ensure_list, [SCENE_SCHEMA]),
    },
    extra=vol.PREVENT_EXTRA,
)

# ─── Gesamtes CONFIG_SCHEMA ───────────────────────────────────────────────────

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.All(cv.ensure_list, [ROUTER_SCHEMA])},
    extra=vol.ALLOW_EXTRA,
)
