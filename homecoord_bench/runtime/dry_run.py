"""Deterministic client used to validate the agent I/O pipeline without an API."""

from __future__ import annotations

import json
from typing import Any

from .protocol import assert_agent_decision


class DryRunClient:
    def decide(self, agent_request: dict[str, Any], instructions: str = "") -> dict[str, Any]:
        task = agent_request["task"]
        agent = agent_request["agent"]
        state_version = agent_request["state_version"]
        acting_role = task.get("agent_id") if agent["agent_id"] == "CentralAgent" else agent["agent_id"]
        episode_id = agent_request.get("base_episode_id", agent_request["episode_id"])
        if acting_role == "EnergyAgent" and task["task_id"] == "energy":
            comfort_visible = agent_request.get("state", {}).get("request", {}).get("comfort_active") is True
            if comfort_visible:
                decision = {
                    "response_type": "action_proposal",
                    "actions": [{
                        "proposal_id": f"{agent_request['request_id']}:0",
                        "target": "living_hvac",
                        "operation": "cool",
                        "parameters": [{"name": "temperature_c", "value_json": "24"}],
                        "based_on_state_version": state_version,
                        "requires": [{"path": "request.comfort_active", "op": "eq", "value_json": "true"}],
                        "estimated_duration_ms": 10000,
                        "estimated_power_kw": 1.2,
                    }],
                    "accepted_proposal_ids": [], "rejected_proposal_ids": [],
                    "defer_until_ms": None, "reason_code": "goal_progress",
                }
                assert_agent_decision(decision)
                return decision
        operation, target, parameters, requirements, duration, power = _action_for(
            episode_id, acting_role, task["task_id"]
        )
        decision = {
            "response_type": "action_proposal",
            "actions": [{
                "proposal_id": f"{agent_request['request_id']}:0",
                "target": target,
                "operation": operation,
                "parameters": [
                    {"name": name, "value_json": json.dumps(value, ensure_ascii=False)}
                    for name, value in parameters.items()
                ],
                "based_on_state_version": state_version,
                "requires": [
                    {"path": item["path"], "op": item["op"], "value_json": json.dumps(item["value"])}
                    for item in requirements
                ],
                "estimated_duration_ms": duration,
                "estimated_power_kw": power,
            }],
            "accepted_proposal_ids": [],
            "rejected_proposal_ids": [],
            "defer_until_ms": None,
            "reason_code": "goal_progress",
        }
        assert_agent_decision(decision)
        return decision


def _action_for(episode_id: str, agent_id: str, task_id: str):
    actions = {
        ("HC-SEED-001", "LightingAgent", "light"): ("set_reading", "study_light", {"lux": 500}, [], 1000, 0.02),
        ("HC-SEED-001", "ClimateAgent", "climate"): ("cool", "bedroom_hvac", {"temperature_c": 25}, [], 3000, 1.2),
        ("HC-SEED-002", "ComfortAgent", "comfort"): ("cool", "living_hvac", {"temperature_c": 24}, [], 10000, 1.4),
        ("HC-SEED-002", "EnergyAgent", "energy"): ("off", "living_hvac", {}, [], 1000, 0.0),
        ("HC-SEED-003", "AirQualityAgent", "air"): ("open", "window", {}, [], 2000, 0.0),
        ("HC-SEED-003", "ClimateAgent", "heat"): ("heat_high", "heater", {}, [], 3000, 2.0),
        ("HC-SEED-004", "CleaningAgent", "clean"): ("clean", "robot", {}, [{"path": "living_room.occupied", "op": "eq", "value": False}], 3000, 0.2),
        ("HC-SEED-004", "CareAgent", "care"): ("update_occupancy", "living_room", {}, [], 100, 0.0),
    }
    return actions[(episode_id, agent_id, task_id)]
