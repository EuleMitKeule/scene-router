"Constants for Scene Router integration."

from enum import StrEnum

DOMAIN = "scene_router"

DATA_SCENE_ROUTERS = "scene_routers"
DATA_CONDITION_VALUES = "condition_values"
DATA_COORDINATORS = "coordinators"
DATA_STORE = "store"

CONF_ENTRY_DEFAULT_NAME = "Scene Router"
CONF_NAME = "name"
CONF_LIGHT_ENTITIES = "light_entities"
CONF_ENABLE_AUTO_CHANGE = "enable_auto_change"
CONF_SCENE_CONFIGS = "scene_configs"
CONF_SCENE = "scene"
CONF_CONDITION = "condition"
CONF_REQUIRED_CUSTOM_CONDITIONS = "required_custom_conditions"
CONF_FORCING_CUSTOM_CONDITIONS = "forcing_custom_conditions"
CONF_ACTION = "action"
CONF_CONDITION_TYPE = "condition_type"

CONF_ERROR_NO_LIGHT_ENTITIES = "no_light_entities"
CONF_ERROR_NO_SCENE_CONFIGS = "no_scene_configs"
CONF_ERROR_SCENE_REQUIRED = "scene_required"
CONF_ERROR_CONDITION_REQUIRED = "condition_required"

DEFAULT_ENABLE_PREVIEW_SENSOR = True
DEFAULT_ENABLE_DEVICE = True
DEFAULT_ENABLE_AUTO_CHANGE = True
DEFAULT_UPDATE_INTERVAL_SECONDS = 10

SIGNAL_ENTRY_UPDATED = "entry_updated"


class ConditionType(StrEnum):
    """Enumeration for condition types."""

    SUN_BELOW = "sun_below"
    TIME_AFTER = "time_after"
