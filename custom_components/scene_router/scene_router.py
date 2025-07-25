"""Scene Router Implementation."""

from __future__ import annotations

import asyncio
from datetime import time
import logging
from typing import Any, TypedDict

from astral.sun import SunDirection, time_at_elevation

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    condition as condition_helper,
    config_validation as cv,
    device_registry as dr,
)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.sun import get_astral_location
from homeassistant.util import dt as dt_util

from .const import DOMAIN, ConditionType
from .models import SceneConfig, SceneRouterConfig

_LOGGER = logging.getLogger(__name__)


class SceneRouter:
    """Scene Router for managing scenes in Home Assistant."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the SceneRouter."""
        self.hass = hass
        self.config_entry = config_entry
        self.scene_router_config: SceneRouterConfig = SceneRouterConfig.from_dict(
            config_entry.options
        )
        self.condition_entities: dict[str, dict[ConditionType, Entity]] = {}

        dr.async_get(hass).async_get_or_create(
            config_entry_id=config_entry.entry_id,
            **self.device_info,
        )

        _LOGGER.debug(
            "SceneRouter initialized for router '%s'", self.scene_router_config.name
        )

    @property
    def device_info(self) -> dr.DeviceInfo:
        """Return the device information for this scene router."""
        return dr.DeviceInfo(
            identifiers={(DOMAIN, self.config_entry.entry_id)},
            name=self.scene_router_config.name,
        )

    @property
    async def selected_scene_entity_id(self) -> str | None:
        """Return the currently selected scene entity ID."""
        entity_id, _ = await self.selected_scene
        if not entity_id:
            _LOGGER.warning(
                "SceneRouter '%s' has no selected scene", self.scene_router_config.name
            )
            return None
        _LOGGER.debug(
            "SceneRouter '%s' selected scene: '%s'",
            self.scene_router_config.name,
            entity_id,
        )
        return entity_id

    @property
    async def selected_scene_friendly_name(self) -> str | None:
        """Return the currently selected scene friendly name."""
        _, friendly_name = await self.selected_scene
        if not friendly_name:
            _LOGGER.warning(
                "SceneRouter '%s' has no selected scene", self.scene_router_config.name
            )
            return None
        _LOGGER.debug(
            "SceneRouter '%s' selected scene: '%s'",
            self.scene_router_config.name,
            friendly_name,
        )
        return friendly_name

    async def _evaluate_custom(self, cfg: dict[str, Any]) -> bool:
        """Compile & evaluate a Home Assistant custom condition dict asynchronously."""
        _LOGGER.debug(
            "Evaluating custom condition: %s for scene: %s",
            cfg,
            self.scene_router_config.name,
        )
        _LOGGER.debug(
            "cfg type: %s, cfg: %s",
            type(cfg),
            cfg,
        )
        cfg = cv.CONDITION_SCHEMA(cfg)
        config = await condition_helper.async_validate_condition_config(self.hass, cfg)
        test = await condition_helper.async_from_config(self.hass, config)
        result = test(self.hass, {})
        if asyncio.iscoroutine(result):
            result = await result
        _LOGGER.debug(
            "Custom condition result for scene '%s': %s",
            self.scene_router_config.name,
            result,
        )
        return bool(result)

    @property
    async def scene_config_candidates(self) -> list[SceneConfig]:
        """Return a list of scene configurations that are candidates for selection."""

        class SceneConfigEvaluation(TypedDict):
            scene_config: SceneConfig
            forcing_conditions_met: bool | None = None
            required_conditions_met: bool | None = None

        evaluations: list[SceneConfigEvaluation] = []
        for scene_config in self.scene_router_config.scene_configs:
            evaluation: SceneConfigEvaluation = {
                "scene_config": scene_config,
            }

            if scene_config.forcing_custom_conditions:
                results = await asyncio.gather(
                    *(
                        self._evaluate_custom(cond)
                        for cond in scene_config.forcing_custom_conditions
                    )
                )
                evaluation["forcing_conditions_met"] = any(results)

            if scene_config.required_custom_conditions:
                results = await asyncio.gather(
                    *(
                        self._evaluate_custom(cond)
                        for cond in scene_config.required_custom_conditions
                    )
                )
                evaluation["required_conditions_met"] = all(results)

            evaluations.append(evaluation)

        if forced_evaluations := [
            evaluation
            for evaluation in evaluations
            if evaluation.get("forcing_conditions_met")
        ]:
            return [evaluation["scene_config"] for evaluation in forced_evaluations]

        return [
            evaluation["scene_config"]
            for evaluation in evaluations
            if evaluation.get("required_conditions_met")
            or evaluation.get("required_conditions_met") is None
        ]

    @property
    async def selected_scene(self) -> tuple[str, str] | None:
        """Asynchronously select the best scene based on required, forcing, and builtin conditions."""
        candidates = await self.scene_config_candidates
        if not candidates:
            _LOGGER.warning(
                "SceneRouter '%s' has no valid scene candidates",
                self.scene_router_config.name,
            )
            return None
        now_dt = dt_util.now()

        class SceneConfigTimelinePoint(TypedDict):
            scene_config: SceneConfig
            from_time: time | None
            to_time: time | None

        scene_config_timeline_points: list[SceneConfigTimelinePoint] = []
        for scene_config in candidates:
            if not (
                condition_entity := self.condition_entities.get(
                    scene_config.scene, {}
                ).get(scene_config.condition)
            ):
                _LOGGER.warning(
                    "Scene '%s' has no condition entity for condition '%s', skipping",
                    scene_config.scene,
                    scene_config.condition,
                )
                continue

            if not (condition_state := condition_entity.state):
                _LOGGER.warning(
                    "Condition entity '%s' for scene '%s' has no state, skipping",
                    condition_entity.entity_id,
                    scene_config.scene,
                )
                continue

            match scene_config.condition:
                case ConditionType.TIME_AFTER:
                    scene_config_timeline_points.append(
                        {
                            "scene_config": scene_config,
                            "from_time": dt_util.parse_time(condition_state),
                        }
                    )
                case ConditionType.SUN_BELOW:
                    try:
                        threshold = float(condition_state)
                        location, _ = get_astral_location(self.hass)
                        elevation_dt = time_at_elevation(
                            location.observer,
                            threshold,
                            date=now_dt.date(),
                            direction=SunDirection.SETTING,
                            tzinfo=now_dt.tzinfo,
                        )
                        scene_config_timeline_points.append(
                            {
                                "scene_config": scene_config,
                                "from_time": elevation_dt.timetz(),
                            }
                        )
                    except ValueError as e:
                        _LOGGER.error(
                            "Invalid sun elevation '%s' for scene '%s': %s",
                            condition_state,
                            scene_config.scene,
                            e,
                        )
                        continue

        scene_config_timeline_points.sort(key=lambda x: (x["from_time"]))

        if not scene_config_timeline_points:
            _LOGGER.warning(
                "SceneRouter '%s' has no valid scene configurations with conditions",
                self.scene_router_config.name,
            )
            return None

        matched_scene_configs: list[SceneConfig] = [
            scene_config_timeline_point["scene_config"]
            for scene_config_timeline_point in scene_config_timeline_points
            if now_dt.timetz() >= scene_config_timeline_point["from_time"]
        ]

        matched_scene_config: SceneConfig
        if not matched_scene_configs:
            matched_scene_config = scene_config_timeline_points[-1]["scene_config"]
        else:
            matched_scene_config = matched_scene_configs[-1]

        scene_state = self.hass.states.get(matched_scene_config.scene)
        scene_entity_id = matched_scene_config.scene
        scene_friendly_name = (
            scene_friendly_name
            if scene_state
            and (scene_friendly_name := scene_state.attributes.get("friendly_name"))
            else scene_entity_id
        )

        return (
            scene_entity_id,
            scene_friendly_name,
        )
