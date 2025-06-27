# custom_components/scene_router/models.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .const import ConditionType


@dataclass
class SceneConfig:
    scene: str
    conditions: list[ConditionType] = field(default_factory=list)


@dataclass
class SceneRouterConfig:
    name: str
    enable_device: bool = True
    enable_preview_sensor: bool = True
    enable_auto_change: bool = True
    lights: list[str] = field(default_factory=list)
    lux_sensors: list[str] = field(default_factory=list)
    scenes: list[SceneConfig] = field(default_factory=list)

    @classmethod
    def load_many(cls, config: dict[str, Any]) -> list[SceneRouterConfig]:
        routers_data = config.get("scene_router", [])
        routers: list[SceneRouterConfig] = []

        for entry in routers_data:
            scenes: list[SceneConfig] = [
                SceneConfig(
                    scene=sc["scene"],
                    conditions=sc.get("conditions", []),
                )
                for sc in entry.get("scenes", [])
            ]

            routers.append(
                SceneRouterConfig(
                    name=entry["name"],
                    enable_device=entry.get("enable_device", True),
                    enable_preview_sensor=entry.get("enable_preview_sensor", True),
                    enable_auto_change=entry.get("enable_auto_change", True),
                    lights=entry.get("lights", []),
                    lux_sensors=entry.get("lux_sensors", []),
                    scenes=scenes,
                )
            )

        return routers
