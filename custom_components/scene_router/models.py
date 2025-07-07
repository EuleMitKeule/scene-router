"""Models for the Scene Router integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .const import (
    CONF_CONDITIONS,
    CONF_ENABLE_AUTO_CHANGE,
    CONF_FORCING_CUSTOM_CONDITION,
    CONF_LIGHT_ENTITIES,
    CONF_NAME,
    CONF_REQUIRED_CUSTOM_CONDITION,
    CONF_SCENE,
    CONF_SCENE_CONFIGS,
    DEFAULT_ENABLE_AUTO_CHANGE,
    ConditionType,
)


@dataclass
class SceneConfig:
    """Configuration for a scene in the Scene Router."""

    scene: str
    conditions: list[ConditionType] = field(default_factory=list)
    forcing_custom_conditions: list[dict[str, Any]] | None = None
    required_custom_conditions: list[dict[str, Any]] | None = None

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> SceneConfig:
        """Create a SceneConfig from a dictionary."""
        return cls(
            scene=value[CONF_SCENE],
            conditions=[
                ConditionType(condition) for condition in value[CONF_CONDITIONS]
            ],
            forcing_custom_conditions=value.get(CONF_FORCING_CUSTOM_CONDITION),
            required_custom_conditions=value.get(CONF_REQUIRED_CUSTOM_CONDITION),
        )


@dataclass
class SceneRouterConfig:
    """Configuration for the Scene Router integration."""

    name: str
    light_entities: list[str]
    scene_configs: list[SceneConfig]
    enable_auto_change: bool = DEFAULT_ENABLE_AUTO_CHANGE

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> SceneRouterConfig:
        """Create a SceneRouterConfig from a dictionary."""

        return cls(
            name=value[CONF_NAME],
            light_entities=value[CONF_LIGHT_ENTITIES],
            scene_configs=[
                SceneConfig.from_dict(scene_config)
                for scene_config in value[CONF_SCENE_CONFIGS]
            ],
            enable_auto_change=value.get(
                CONF_ENABLE_AUTO_CHANGE, DEFAULT_ENABLE_AUTO_CHANGE
            ),
        )
