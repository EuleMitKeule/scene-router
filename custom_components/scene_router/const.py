"Constants for Scene Router integration."

from enum import StrEnum

DOMAIN = "scene_router"

DATA_SCENE_ROUTERS = "scene_routers"

CONF_ENTRY_DEFAULT_NAME = "Scene Router"
CONF_NAME = "name"
CONF_LIGHT_ENTITIES = "light_entities"
CONF_ENABLE_PREVIEW_SENSOR = "enable_preview_sensor"
CONF_ENABLE_AUTO_CHANGE = "enable_auto_change"

CONF_ERROR_NO_LIGHT_ENTITIES = "no_light_entities"


class ConditionType(StrEnum):
    """Enumeration for condition types."""

    LUX_ABOVE = "lux_above"
    LUX_BELOW = "lux_below"
    ELEVATION_ABOVE = "elevation_above"
    ELEVATION_BELOW = "elevation_below"
    TIME_BEFORE = "time_before"
    TIME_AFTER = "time_after"
