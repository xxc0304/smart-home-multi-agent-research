"""Offline-only projection of four frozen development tasks; never sends requests."""
import argparse
import hashlib
import json
import random
from pathlib import Path

PROJECT=Path(__file__).resolve().parents[1]
SOURCE=PROJECT/"data/task-source-audit-20261021/hiddenbench.json"
SELECTION=PROJECT/"data/dataset-selection-20261022/SELECTION_MANIFEST.json"
DEV_IDS=(1,4,34,50)


def read(path): return json.loads(path.read_text(encoding="utf-8"))


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


def build(output, *, dev_ids=DEV_IDS):
    dev_ids=tuple(dev_ids)
    if not dev_ids or len(set(dev_ids))!=len(dev_ids): raise ValueError("Unique development IDs required")
    selection=read(SELECTION)
    sha=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if sha!=selection["source_sha256"]: raise ValueError("Source differs from fixed snapshot")
    if not set(dev_ids)<=set(selection["development_ids"]): raise ValueError("Not in development split")
    if output.exists(): raise ValueError("Output must be new")
    records={int(r["id"]):r for r in read(SOURCE)}
    manifest={"kind":"hiddenbench_four_development_tasks","source_sha256":sha,
              "ids":list(dev_ids),"selection_based_on_model_results":False,"tasks":[],"network_requests":0}
    for number in dev_ids:
        source=records[number];hidden=source["hidden_information"]
        if len(hidden) not in {3,4} or not all(isinstance(s,str) and s.strip() for s in hidden):
            raise ValueError("Unexpected native member packets")
        choices=list(source["possible_answers"])
        if len(set(choices))!=len(choices) or source["correct_answer"] not in choices:
            raise ValueError("Invalid official answer mapping")
        random.Random(f"hiddenbench-dev-choice-v1-{number}").shuffle(choices)
        options=[{"id":f"option_{i}","text":label} for i,label in enumerate(choices,1)]
        anonymous=f"hb-dev-{number:03d}"
        task={"task_id":anonymous,"task_type":"choice","title":"Collective decision task",
              "scenario":source["description"],"shared_information":source["shared_information"],
              "instruction":"Choose one option using the available facts. State the reasoning and any unresolved limits.",
              "choices":options,"output_contract":"artifact must be one option ID, not an option text or ranking; null only if no answer can be offered."}
        team=[f"A{i}" for i in range(1,len(hidden)+1)]
        materials=[{"ref":f"S{i:02d}","content":content} for i,content in enumerate(hidden,1)]
        pack=output/anonymous
        for condition in ("distributed","all_information","shared_only"):
            allocation={a:([materials[i]] if condition=="distributed" else materials if condition=="all_information" else [])
                        for i,a in enumerate(team)}
            directory=[{"agent_id":a,"accessible_materials":[{"ref":m["ref"]} for m in allocation[a]]} for a in team]
            for agent in team:
                packet={"TASK":task,"SELF":{"agent_id":agent,"team":team},"SELF_MATERIALS":allocation[agent],
                        "DIRECTORY":directory,"REFERENCE_INDEX":[{"ref":"T","kind":"task"}]
                        +[{"ref":m["ref"],"kind":"private_material"} for m in allocation[agent]]}
                write(pack/"packets"/condition/f"{agent}.json",packet)
        # Never included in member packets. Runtime has no reason to open this file.
        write(pack/"offline/evaluation.json",{"task_id":anonymous,"source_id":number,
              "source_name":source["name"],"official_correct_text":source["correct_answer"],
              "correct_option_id":next(c["id"] for c in options if c["text"]==source["correct_answer"]),
              "choices":options,"metric":"single_team_exact_match_not_original_all_member_voting"})
        write(pack/"public/task.json",task)
        manifest["tasks"].append({"task_id":anonymous,"members":len(team),"pack":anonymous})
    manifest["file_hashes"]={str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in sorted(output.rglob("*.json"))}
    write(output/"dataset_manifest.json",manifest)
    return manifest


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args();m=build(args.output)
    print(json.dumps({"tasks":len(m["tasks"]),"members":[t["members"] for t in m["tasks"]],"network_requests":0}))
