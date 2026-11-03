"""Strict choice packet loading, reusing the existing no-evaluator packet loader."""
import re

from ..handoff.inputs import Packets as BasePackets, exact, text
from ..schemas import ProtocolError


class ChoicePackets(BasePackets):
    @staticmethod
    def _validate(p):
        exact(p, {"TASK", "SELF", "SELF_MATERIALS", "DIRECTORY", "REFERENCE_INDEX"}, "packet")
        task = p["TASK"]
        exact(task, {"task_id", "task_type", "title", "scenario", "shared_information", "instruction",
                     "choices", "output_contract"}, "TASK")
        if task["task_type"] != "choice": raise ProtocolError("INPUT_ERROR", "Expected choice task")
        for key in ("task_id", "title", "scenario", "instruction", "output_contract"): text(task[key], key)
        if not isinstance(task["shared_information"], list): raise ProtocolError("INPUT_ERROR", "Expected shared fact list")
        for fact in task["shared_information"]: text(fact, "shared fact")
        if not isinstance(task["choices"], list) or len(task["choices"]) < 2:
            raise ProtocolError("INPUT_ERROR", "Expected two or more choices")
        ids, labels = set(), set()
        for c in task["choices"]:
            exact(c, {"id", "text"}, "choice"); text(c["text"], "choice text")
            if not isinstance(c["id"], str) or not re.fullmatch(r"option_[1-9][0-9]*", c["id"]):
                raise ProtocolError("INPUT_ERROR", "Invalid option ID")
            if c["id"] in ids or c["text"] in labels: raise ProtocolError("INPUT_ERROR", "Duplicate choice")
            ids.add(c["id"]); labels.add(c["text"])
        exact(p["SELF"], {"agent_id", "team"}, "SELF"); team=p["SELF"]["team"]
        if (not isinstance(team, list) or len(team) not in {3, 4}
                or not all(isinstance(a,str) and re.fullmatch(r"A[1-9][0-9]*",a) for a in team)
                or len(set(team)) != len(team)
                or p["SELF"]["agent_id"] not in team):
            raise ProtocolError("INPUT_ERROR", "Expected a three/four member roster")
        directory = {}
        for key in ("DIRECTORY","SELF_MATERIALS","REFERENCE_INDEX"):
            if not isinstance(p[key],list): raise ProtocolError("INPUT_ERROR",f"{key} must be a list")
        for row in p["DIRECTORY"]:
            exact(row, {"agent_id", "accessible_materials"}, "directory")
            if not isinstance(row["agent_id"],str) or row["agent_id"] not in team or row["agent_id"] in directory:
                raise ProtocolError("INPUT_ERROR", "Invalid directory member")
            if not isinstance(row["accessible_materials"],list): raise ProtocolError("INPUT_ERROR","Expected material list")
            refs=[]
            for material in row["accessible_materials"]:
                exact(material, {"ref"}, "directory material")
                if not isinstance(material["ref"],str) or not re.fullmatch(r"S[0-9]+",material["ref"]):
                    raise ProtocolError("INPUT_ERROR", "Invalid material ref")
                refs.append(material["ref"])
            if len(set(refs)) != len(refs): raise ProtocolError("INPUT_ERROR", "Duplicate directory ref")
            directory[row["agent_id"]] = set(refs)
        if set(directory) != set(team): raise ProtocolError("INPUT_ERROR", "Directory roster mismatch")
        own=set()
        for material in p["SELF_MATERIALS"]:
            exact(material, {"ref", "content"}, "private material");text(material["content"], "material content")
            if not isinstance(material["ref"],str) or not re.fullmatch(r"S[0-9]+",material["ref"]):
                raise ProtocolError("INPUT_ERROR","Invalid own material ref")
            if material["ref"] in own: raise ProtocolError("INPUT_ERROR", "Duplicate own ref")
            own.add(material["ref"])
        if own != directory[p["SELF"]["agent_id"]]: raise ProtocolError("INPUT_ERROR", "Own materials mismatch")
        refs={}
        for entry in p["REFERENCE_INDEX"]:
            exact(entry, {"ref", "kind"}, "reference")
            text(entry["ref"],"reference ref");text(entry["kind"],"reference kind")
            if entry["ref"] in refs: raise ProtocolError("INPUT_ERROR", "Duplicate reference")
            refs[entry["ref"]]=entry["kind"]
        if refs != {"T":"task", **{ref:"private_material" for ref in own}}:
            raise ProtocolError("INPUT_ERROR", "Unaccessible reference in index")
