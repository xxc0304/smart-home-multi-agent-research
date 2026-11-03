"""Bounded, frozen two-task development pilot; no initial-answer generation."""
import argparse
import copy
import json
from pathlib import Path
import time
from tokenizers import Tokenizer
from coreta.model_client import DeepSeekClient
from coreta.schemas import ProtocolError
import local_judgment_frontend as io
import local_judgment_handle_contract as handles
import local_rule_team_integration as team
import prepare_local_rule_adoption as adoption
import evidence_first_frontend as frontend

ROOT=io.ROOT
DATA=ROOT/"data/task-packs/hiddenbench-local-contribution-dev-20261025-v1"
HISTORY=ROOT/"runs/hb-local-contribution-live-20261025-r1"
TOKENIZER=ROOT/"data/tokenizer-v4.1-flash-1017/tokenizer.json"
RUBRIC=ROOT/"design/EVIDENCE_FIRST_PILOT_20261025.md"
TASKS=("hb-local-dev-005","hb-local-dev-009")
MEMBERS=("A1","A2","A3","A4")
MAX_REQUESTS,CAP,TOTAL_CAP,INPUT_CAP=72,1536,110592,393216
VERSION="evidence-first-pilot/1"


def child(root,name):
    p=(Path(root)/name).resolve()
    if not p.is_relative_to(Path(root).resolve()):
        raise ValueError("path escapes root")
    return p


def schedule():
    rows=[]
    for idx,task in enumerate(TASKS):
        for repeat in (1,2):
            unit=f"{task}/r{repeat}"
            order=frontend.METHODS if (idx+repeat)%2 else frontend.METHODS[::-1]
            for method in order:
                for member in MEMBERS:
                    for stage in ("first","second"):
                        rows.append(dict(task=task,repeat=repeat,unit=unit,method=method,member=member,
                                         stage=stage,group=f"{unit}/{method}/{member}"))
                rows.append(dict(task=task,repeat=repeat,unit=unit,method=method,member=None,
                                 stage="integrate",group=f"{unit}/{method}"))
    return [dict(row,slot=i) for i,row in enumerate(rows,1)]


def config():
    return dict(provider="deepseek",model="deepseek-flash",base_url="https://api.deepseek.com",
                generation=dict(reasoning_effort="none",temperature=0.7,max_input_tokens=32768),
                protocol=dict(transport_retries_per_request=0,max_format_repairs=0,request_timeout_seconds=120))


def freeze(output):
    p=Path(output)
    if p.exists():
        raise ValueError("new prepared directory required")
    source=io.read(DATA/"dataset_manifest.json")
    for rel,sha in source["files"].items():
        if io.digest(child(DATA,rel))!=sha:
            raise ValueError("source changed: "+rel)
    p.mkdir(parents=True)
    provenance=[]
    for task in TASKS:
        for member in MEMBERS:
            src=DATA/task/"packets/distributed"/f"{member}.json"
            io.write(p/"contexts"/task/f"{member}.json",io.read(src))
            provenance.append(dict(path=str(src.relative_to(ROOT)),sha256=io.digest(src)))
        for repeat in (1,2):
            src=HISTORY/"common_drafts"/task/f"r{repeat}.json"
            io.write(p/"drafts"/task/f"r{repeat}.json",io.read(src))
            provenance.append(dict(path=str(src.relative_to(ROOT)),sha256=io.digest(src),kind="unchanged actual public-only W0"))
        (p/f"OFFLINE_{task}.json").write_bytes((DATA/task/"offline/evaluation.json").read_bytes())
    io.write(p/"SOURCE_PROVENANCE.json",provenance)
    io.write(p/"PLAN.json",dict(status="FROZEN_NOT_AUTHORIZED",tasks=list(TASKS),members=list(MEMBERS),repeats=2,
             schedule=schedule(),max_requests=MAX_REQUESTS,max_output_tokens=TOTAL_CAP,max_input_tokens=INPUT_CAP,
             initial_requests=0,draft_origin="4 actual archived public-only W0s; no answer repair or selection by new outcomes",
             method_difference="Complete candidate: independent local formation, delayed W0 and subsequent evidence-to-draft connection.",
             shared_changes="Strict output contract, multiple findings permitted, first-view pass still enters second view."))
    io.write(p/"config.json",config())
    (p/"SCORING_AND_PLAN.md").write_bytes(RUBRIC.read_bytes())
    code=[Path(__file__),Path(frontend.__file__),Path(io.__file__),Path(handles.__file__),Path(team.__file__),
          Path(adoption.__file__),ROOT/"src/coreta/model_client.py",ROOT/"src/coreta/schemas.py",
          ROOT/"tools/export_evidence_first_pilot.py"]
    io.write(p/"manifest.json",dict(version=VERSION,max_requests=MAX_REQUESTS,output_cap=CAP,total_output_cap=TOTAL_CAP,total_input_cap=INPUT_CAP,
             tokenizer_sha256=io.digest(TOKENIZER),
             files={str(x.relative_to(p)).replace("\\","/"):io.digest(x) for x in p.rglob("*") if x.is_file()},
             code_sha256={str(x.relative_to(ROOT)).replace("\\","/"):io.digest(x) for x in code}))
    verify(p)
    return dict(status="FROZEN_NOT_AUTHORIZED",manifest_sha256=io.digest(p/"manifest.json"))


def verify(prepared):
    p=Path(prepared);m=io.read(p/"manifest.json")
    if (m["version"],m["max_requests"],m["output_cap"],m["total_output_cap"],m["total_input_cap"])!=(VERSION,MAX_REQUESTS,CAP,TOTAL_CAP,INPUT_CAP):
        raise ValueError("batch or budget differs")
    for root,files in ((p,m["files"]),(ROOT,m["code_sha256"])):
        for rel,sha in files.items():
            if io.digest(child(root,rel))!=sha:
                raise ValueError("frozen file changed: "+rel)
    if io.digest(TOKENIZER)!=m["tokenizer_sha256"]:
        raise ValueError("tokenizer changed")
    plan=io.read(p/"PLAN.json")
    if plan["schedule"]!=schedule() or io.read(p/"config.json")!=config():
        raise ValueError("plan/config differs")
    for task in TASKS:
        base=io.read(p/"contexts"/task/"A1.json")
        for member in MEMBERS:
            x=io.read(p/"contexts"/task/f"{member}.json")
            if set(x)!={"task","member","public_sources","own_sources"} or x["member"]!=member:
                raise ValueError("context contract differs")
            if x["task"]!=base["task"] or x["public_sources"]!=base["public_sources"] or [s["ref"] for s in x["own_sources"]]!=[member+".S1"]:
                raise ValueError("member privacy differs")
        for repeat in (1,2):
            d=io.read(p/"drafts"/task/f"r{repeat}.json")
            if not d["reason"].strip() or not isinstance(d["claims"],list):
                raise ValueError("cached draft unreadable")
    return m,plan


def gates(prepared):
    p=Path(prepared);sha=io.digest(p/"manifest.json")
    pre=io.read(p/"PREFLIGHT.json");review=io.read(p/"EXPERIMENT_REVIEW.json");auth=io.read(p/"AUTHORIZATION.json")
    if pre.get("status")!="passed" or pre.get("manifest_sha256")!=sha:
        raise ValueError("fresh preflight required")
    if any(review.get(k)!=v for k,v in dict(science="PASS",readiness="PASS",technical_launch="RUN_ALLOWED",manifest_sha256=sha).items()):
        raise ValueError("fresh review required")
    expected=dict(authorized=True,max_requests=MAX_REQUESTS,max_output_tokens=TOTAL_CAP,max_input_tokens=INPUT_CAP,
                  destination="https://api.deepseek.com/responses",manifest_sha256=sha)
    if any(auth.get(k)!=v for k,v in expected.items()) or not auth.get("user_authorization_text"):
        raise ValueError("specific batch authorization required")


def packet_for(p,row,firsts,deliveries):
    draft=io.read(p/"drafts"/row["task"]/f"r{row['repeat']}.json")
    if row["stage"]=="integrate":
        final=deliveries.get(row["group"],{})
        if set(final)!=set(MEMBERS):
            return None,"blocked_upstream"
        packets=[io.read(p/"contexts"/row["task"]/f"{member}.json") for member in MEMBERS]
        return team.assemble(packets[0]["task"],packets[0]["public_sources"],draft,packets,final),None
    base=io.read(p/"contexts"/row["task"]/f"{row['member']}.json")
    if row["stage"]=="first":
        if row["method"]=="ordinary":
            base["historical_work"]=copy.deepcopy(draft)
        return base,None
    first=firsts.get(row["group"])
    if first is None:
        return None,"blocked_upstream"
    return frontend.second_packet(base,first,row["method"],draft),None


def make_request(row,packet):
    return frontend.integration_request(packet) if row["stage"]=="integrate" else frontend.request(row["stage"],row["method"],packet)


def run(prepared,output,*,transport=None,local_validation=False):
    p,out=Path(prepared),Path(output);manifest,plan=verify(p)
    if local_validation:
        if transport is None:
            raise ValueError("explicit local transport required")
    else:
        gates(p)
    if out.exists():
        raise ValueError("new output required; no resume")
    out.mkdir(parents=True);io.write(out/"manifest.json",manifest)
    state=dict(mode="local_fixture" if local_validation else "live",status="running",attempts=0,input_tokens=0,output_tokens=0,
               reserved_output=0,reserved_estimated_input=0,unknown_usage=False,consecutive_unreadable=0,rows=[],error=None)
    firsts,deliveries={},{};current=None;roster=plan["schedule"]
    def save():
        io.write(out/"progress.json",state)
        done={r["slot"]:r for r in state["rows"]}
        io.write(out/"review.json",dict(mode=state["mode"],status=state["status"],
                 rows=[done.get(r["slot"],dict(r,status="not_run",answer=None)) for r in roster]))
    def log(name,value):
        with (out/name).open("a",encoding="utf-8") as f:
            f.write(json.dumps(value,ensure_ascii=False)+"\n")
        if name!="responses.jsonl":
            return
        response=value.get("response")
        if response is None:
            state["unknown_usage"]=True;return
        text="".join(part["text"] for item in response.get("output",[]) if item.get("type")=="message"
                     for part in item.get("content",[]) if part.get("type")=="output_text" and isinstance(part.get("text"),str))
        if text:
            (out/f"{current:03d}.raw.txt").write_text(text,encoding="utf-8")
        for field in ("input_tokens","output_tokens"):
            amount=response.get("usage",{}).get(field)
            if type(amount) is not int or amount<0:
                state["unknown_usage"]=True
            else:
                state[field]+=amount
                if field=="output_tokens" and amount>CAP:
                    state["over_cap"]=True
    tokenizer=Tokenizer.from_file(str(TOKENIZER))
    client=DeepSeekClient(config(),log,transport=transport,token_counter=lambda s:len(tokenizer.encode(s,add_special_tokens=False).ids))
    save()
    try:
        for row in roster:
            current=row["slot"];packet,blocked=packet_for(p,row,firsts,deliveries)
            if blocked:
                state["rows"].append(dict(row,status=blocked,answer=None));save();continue
            req=make_request(row,packet);payload=client.payload(req["instructions"],req["schema"],CAP)
            amount=client.size(payload)
            if client.attempts>=MAX_REQUESTS or state["reserved_output"]+CAP>TOTAL_CAP or state["reserved_estimated_input"]+amount>INPUT_CAP:
                raise RuntimeError("pre-request budget exceeded")
            io.write(out/"actual_requests"/f"{current:03d}.json",req)
            state["reserved_output"]+=CAP;state["reserved_estimated_input"]+=amount
            try:
                raw=client.complete(payload,deadline=time.monotonic()+180,logical_seed=row["repeat"])
                if state["unknown_usage"]:
                    raise RuntimeError("unknown usage")
                if state.get("over_cap") or state["output_tokens"]>state["reserved_output"] or state["input_tokens"]>INPUT_CAP:
                    raise RuntimeError("actual budget exceeded")
                answer=frontend.decode_integration(raw,packet) if row["stage"]=="integrate" else frontend.decode(raw,row["stage"],packet)
            except (ValueError,ProtocolError) as exc:
                unreadable=isinstance(exc,ValueError) or (isinstance(exc,ProtocolError) and exc.code=="SCHEMA_ERROR")
                if not unreadable or state["unknown_usage"] or state.get("over_cap"):
                    raise
                state["rows"].append(dict(row,status="quarantined",answer=None,error=str(exc)))
                state["consecutive_unreadable"]+=1;state["attempts"]=client.attempts;save()
                if state["consecutive_unreadable"]>=2:
                    raise RuntimeError("two consecutive unreadable outputs") from exc
                continue
            if row["stage"]=="first":
                firsts[row["group"]]=answer
            elif row["stage"]=="second":
                deliveries.setdefault(f"{row['unit']}/{row['method']}",{})[row["member"]]=answer
            state["rows"].append(dict(row,status="readable",answer=answer))
            state["consecutive_unreadable"]=0;state["attempts"]=client.attempts;save()
        state["status"]="completed_with_quarantine" if any(r["status"]=="quarantined" for r in state["rows"]) else "completed"
    except Exception as exc:
        if current is not None and not any(r["slot"]==current for r in state["rows"]):
            state["rows"].append(dict(roster[current-1],status="failed",answer=None))
        state.update(status="stopped",error_type=type(exc).__name__,error=str(exc));raise
    finally:
        state["attempts"]=client.attempts;save()
    return state


def preflight(prepared):
    p=Path(prepared);_,plan=verify(p);history=io.read(HISTORY/"review.json")["rows"]
    tokenizer=Tokenizer.from_file(str(TOKENIZER))
    count=lambda text:len(tokenizer.encode(text,add_special_tokens=False).ids)
    def replay_run(name,stress):
        trace=[]
        def replay(payload,timeout):
            row=plan["schedule"][len(trace)]
            old=next(r for r in history if r["task"]==row["task"] and r["repeat"]==row["repeat"]
                     and r["member"]==row["member"] and r["stage"]==row["stage"] and r["method"]=="ordinary")
            path=HISTORY/f"{old['slot']:03d}.raw.txt"
            original=io.read(path)
            if row["stage"]=="first":
                original={k:original[k] for k in ("text","status","source_ids")}
            if stress and row["stage"]!="integrate":
                field="text" if row["stage"]=="first" else "conclusion"
                # Preserve the full original, then repeat complete sentences for a
                # synthetic near-cap load fixture; never edit a live response.
                extra=[s.strip()+"." for s in original[field].split(". ") if s.strip()]
                for _ in range(20):
                    grew=False
                    for sentence in extra:
                        candidate=dict(original,**{field:original[field]+"\n"+sentence})
                        if count(json.dumps(candidate,ensure_ascii=False))<=CAP:
                            original=candidate;grew=True
                    if not grew:
                        break
            raw=json.dumps(original,ensure_ascii=False)
            assert count(raw)<=CAP
            trace.append(dict(slot=row["slot"],source=str(path.relative_to(ROOT)),sha256=io.digest(path),
                              fixture_output_tokens=count(raw),synthetic_extension=stress and row["stage"]!="integrate",
                              adaptation="First removes unused target_ids metadata only. Normal replay preserves all substantive text. Stress replay additionally repeats complete historical sentences to approach cap; no new correct fact or answer inserted. These are technical fixtures, not new candidate behavior."))
            return dict(status="completed",usage=dict(input_tokens=10,output_tokens=10),
                        output=[dict(type="message",content=[dict(type="output_text",text=raw)])])
        result=run(p,p/name,transport=replay,local_validation=True)
        assert result["status"]=="completed" and result["attempts"]==72
        reqs=[io.strict_json(line) for line in (p/name/"requests.jsonl").read_text(encoding="utf-8").splitlines()]
        return trace,reqs
    trace,reqs=replay_run("history_replay",False)
    stress_trace,stress_reqs=replay_run("stress_replay",True)
    report=dict(status="passed",manifest_sha256=io.digest(p/"manifest.json"),live_model_requests=0,
                replay_requests=72,maximum_input_estimate=max(r["estimated_input_count"] for r in reqs),
                total_input_estimate=sum(r["estimated_input_count"] for r in reqs),trace=trace,
                stress_fixture_requests=72,stress_maximum_input_estimate=max(r["estimated_input_count"] for r in stress_reqs),
                stress_total_input_estimate=sum(r["estimated_input_count"] for r in stress_reqs),
                stress_maximum_fixture_output=max(r["fixture_output_tokens"] for r in stress_trace),stress_trace=stress_trace,
                limitations=["Full real historical responses validate interface and dynamic load, not candidate semantics or provider compliance.",
                             "Stress output extensions are explicitly synthetic; tested payloads are not a proof covering every possible token sequence."])
    io.write(p/"PREFLIGHT.json",report)
    return {k:v for k,v in report.items() if k not in ("trace","stress_trace")}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=["freeze","preflight","run"])
    parser.add_argument("--prepared",type=Path,required=True)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    if args.command=="freeze":
        print(json.dumps(freeze(args.prepared)))
    elif args.command=="preflight":
        print(json.dumps(preflight(args.prepared)))
    else:
        if args.output is None:
            parser.error("--output required")
        run(args.prepared,args.output)
