"""Number platform for Scene Router integration."""

from collections import Counter, defaultdict
import logging

from config.custom_components.scene_router.scene_router import SceneRouter
from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_SCENE_ROUTERS, DOMAIN, ConditionType
from .entity import SceneRouterEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number platform for Scene Router integration."""
    _LOGGER.debug("Setting up number platform for Scene Router integration")

    scene_routers: list[SceneRouter] = hass.data.get(DOMAIN, {}).get(
        DATA_SCENE_ROUTERS, []
    )

    if not scene_routers:
        _LOGGER.debug(
            "No SceneRouter instances found in hass.data, skipping number platform"
        )
        return

    for scene_router in scene_routers:
        entity_descriptions: list[NumberEntityDescription] = []

        for scene_config in scene_router.config.scenes:
            counts = Counter(scene_config.conditions)
            indices: dict[ConditionType, int] = defaultdict(int)

            for condition in scene_config.conditions:
                indices[condition] += 1
                suffix = f"_{indices[condition]}" if counts[condition] > 1 else ""

                match condition:
                    case ConditionType.LUX_ABOVE:
                        key = f"{scene_config.scene}_lux_above{suffix}"
                        translation_key = "lux_above"
                    case ConditionType.LUX_BELOW:
                        key = f"{scene_config.scene}_lux_below{suffix}"
                        translation_key = "lux_below"
                    case ConditionType.ELEVATION_ABOVE:
                        key = f"{scene_config.scene}_elevation_above{suffix}"
                        translation_key = "elevation_above"
                    case ConditionType.ELEVATION_BELOW:
                        key = f"{scene_config.scene}_elevation_below{suffix}"
                        translation_key = "elevation_below"

                entity_descriptions.append(
                    NumberEntityDescription(
                        key=key,
                        translation_key=translation_key,
                        entity_category=EntityCategory.CONFIG,
                    )
                )

        for entity_description in entity_descriptions:
            async_add_entities(
                [
                    SceneRouterNumberEntity(
                        config_entry,
                        scene_router,
                        entity_description,
                    )
                ]
            )


class SceneRouterNumberEntity(SceneRouterEntity, NumberEntity):
    """Number entity for Scene Router integration."""
