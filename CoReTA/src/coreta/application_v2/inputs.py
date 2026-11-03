"""V2 ranking packet validation; inherited loading keeps evaluator data isolated.

Validation body follows frozen handoff invariants, extending only candidate count.
"""
import re
from ..schemas import ProtocolError
from ..handoff.inputs import Packets as FrozenPackets, exact, text, read_json


class Packets(FrozenPackets):
    @staticmethod
    def _validate(p):
        exact(p, {"TASK", "SELF", "SELF_MATERIALS", "DIRECTORY", "REFERENCE_INDEX"}, "packet")
        exact(p["TASK"], {"task_id", "task_type", "title", "scenario", "instruction", "items", "output_contract"}, "TASK")
        task = p["TASK"]
        if task["task_type"] != "ranking":
            raise ProtocolError("INPUT_ERROR", "Only ranking task packets are supported")
        for key in ("task_id", "title", "scenario", "instruction", "output_contract"):
            text(task[key], f"TASK.{key}")
        if not isinstance(task["items"], list) or len(task["items"]) not in {4, 15}:
            raise ProtocolError("INPUT_ERROR", "Expected 4 or 15 public items")
        for item in task["items"]:
            exact(item, {"item_id", "name"}, "TASK.items[]")
            for val in item.values():
                text(val, "TASK.items[]")
        names = {i["name"] for i in task["items"]}
        ids = {i["item_id"] for i in task["items"]}
        if len(names) != len(task["items"]) or len(ids) != len(task["items"]):
            raise ProtocolError("INPUT_ERROR", "Public items must be unique")
        item_names = {i["item_id"]: i["name"] for i in task["items"]}
        exact(p["SELF"], {"agent_id", "team"}, "SELF")
        team = p["SELF"]["team"]
        if (not isinstance(team, list) or not all(isinstance(a, str) and re.fullmatch(r"A[1-9][0-9]*", a) for a in team)
                or len(team) < 2 or len(set(team)) != len(team) or p["SELF"]["agent_id"] not in team):
            raise ProtocolError("INPUT_ERROR", "Invalid member roster")
        for key in ("SELF_MATERIALS", "DIRECTORY", "REFERENCE_INDEX"):
            if not isinstance(p[key], list):
                raise ProtocolError("INPUT_ERROR", f"{key} must be a list")
        directory = {}
        for row in p["DIRECTORY"]:
            exact(row, {"agent_id", "accessible_materials"}, "DIRECTORY[]")
            if row["agent_id"] not in team or row["agent_id"] in directory or not isinstance(row["accessible_materials"], list):
                raise ProtocolError("INPUT_ERROR", "Invalid directory member")
            mapping = {}
            for material in row["accessible_materials"]:
                exact(material, {"ref", "item_id", "item_name"}, "directory material")
                text(material["item_id"], "directory material.item_id")
                text(material["item_name"], "directory material.item_name")
                if (not isinstance(material["ref"], str) or not re.fullmatch(r"S[0-9]+", material["ref"])
                        or material["ref"] in mapping or item_names.get(material["item_id"]) != material["item_name"]):
                    raise ProtocolError("INPUT_ERROR", "Invalid directory material")
                mapping[material["ref"]] = material
            directory[row["agent_id"]] = mapping
        if set(directory) != set(team):
            raise ProtocolError("INPUT_ERROR", "Directory does not match roster")
        own = {}
        for material in p["SELF_MATERIALS"]:
            exact(material, {"ref", "item_id", "item_name", "content"}, "private material")
            for key in ("ref", "item_id", "item_name"):
                text(material[key], f"private material.{key}")
            text(material["content"], "material.content")
            if material["ref"] in own:
                raise ProtocolError("INPUT_ERROR", "Duplicate private material")
            own[material["ref"]] = {k: v for k, v in material.items() if k != "content"}
        if own != directory[p["SELF"]["agent_id"]]:
            raise ProtocolError("INPUT_ERROR", "Private payload disagrees with directory")
        refs = {}
        for entry in p["REFERENCE_INDEX"]:
            exact(entry, {"ref", "kind"}, "REFERENCE_INDEX[]")
            text(entry["ref"], "REFERENCE_INDEX.ref")
            text(entry["kind"], "REFERENCE_INDEX.kind")
            if entry["ref"] in refs:
                raise ProtocolError("INPUT_ERROR", "Duplicate visible reference")
            refs[entry["ref"]] = entry["kind"]
        if refs != {"T": "task", **{ref: "private_material" for ref in own}}:
            raise ProtocolError("INPUT_ERROR", "Reference index includes unread sources")
