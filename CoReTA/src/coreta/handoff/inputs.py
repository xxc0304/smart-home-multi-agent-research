"""Strict packet projection. This module never reads a reference ranking."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path

from ..schemas import ProtocolError


def read_json(path: Path):
    def pairs(entries):
        result = {}
        for key, value in entries:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)


def exact(value, fields, location):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ProtocolError("INPUT_ERROR", f"{location}: expected exactly {sorted(fields)}")


def text(value, location):
    if not isinstance(value, str) or not value.strip():
        raise ProtocolError("INPUT_ERROR", f"{location}: expected nonempty string")


class Packets:
    def __init__(self, root: Path, condition: str):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", condition):
            raise ProtocolError("INPUT_ERROR", "Invalid condition identifier")
        self.root, self.condition = root.resolve(), condition
        folder = self.root / "packets" / condition
        paths = sorted(folder.glob("*.json"))
        if not paths:
            raise ProtocolError("INPUT_ERROR", "No member packets in selected condition")
        self.members, self.hashes = {}, {}
        for path in paths:
            if not path.resolve().is_relative_to(self.root):
                raise ProtocolError("INPUT_ERROR", "Packet path escapes task pack")
            packet = read_json(path)
            self._validate(packet)
            member = packet["SELF"]["agent_id"]
            if member in self.members or path.stem != member:
                raise ProtocolError("INPUT_ERROR", "Duplicate member or filename/member mismatch")
            self.members[member] = packet
            self.hashes[str(path.relative_to(self.root))] = hashlib.sha256(path.read_bytes()).hexdigest()
        first = next(iter(self.members.values()))
        self.agents, self.task = first["SELF"]["team"], first["TASK"]
        self.directory = first["DIRECTORY"]
        if set(self.members) != set(self.agents):
            raise ProtocolError("INPUT_ERROR", "Missing or additional team packet")
        for packet in self.members.values():
            if (packet["TASK"] != self.task or packet["DIRECTORY"] != self.directory
                    or packet["SELF"]["team"] != self.agents):
                raise ProtocolError("INPUT_ERROR", "Inconsistent task/team/directory across members")
        self.owners = {}
        for row in self.directory:
            for material in row["accessible_materials"]:
                self.owners.setdefault(material["ref"], set()).add(row["agent_id"])
        contents = {}
        for packet in self.members.values():
            for material in packet["SELF_MATERIALS"]:
                previous = contents.setdefault(material["ref"], material)
                if previous != material:
                    raise ProtocolError("INPUT_ERROR", "Shared material handle has inconsistent contents")

    @staticmethod
    def _validate(p):
        exact(p, {"TASK", "SELF", "SELF_MATERIALS", "DIRECTORY", "REFERENCE_INDEX"}, "packet")
        exact(p["TASK"], {"task_id", "task_type", "title", "scenario", "instruction", "items", "output_contract"}, "TASK")
        task = p["TASK"]
        if task["task_type"] != "ranking":
            raise ProtocolError("INPUT_ERROR", "Only ranking task packets are supported")
        for key in ("task_id", "title", "scenario", "instruction", "output_contract"):
            text(task[key], f"TASK.{key}")
        if not isinstance(task["items"], list) or len(task["items"]) != 15:
            raise ProtocolError("INPUT_ERROR", "Expected 15 public items")
        for item in task["items"]:
            exact(item, {"item_id", "name"}, "TASK.items[]")
            for val in item.values():
                text(val, "TASK.items[]")
        names = {i["name"] for i in task["items"]}
        ids = {i["item_id"] for i in task["items"]}
        if len(names) != 15 or len(ids) != 15:
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

    def member(self, agent):
        return copy.deepcopy(self.members[agent])
