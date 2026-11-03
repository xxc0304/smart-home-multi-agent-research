"""Post-run audit. Keeps frozen interface scores separate from raw-answer forensics."""
import collections
import json
from pathlib import Path
import shutil
import evidence_first_frontend as frontend
import export_evidence_first_pilot as scorer
import minimal_final_answer_contract as future_contract
import local_judgment_frontend as io
import run_evidence_first_pilot as runner

ROOT=io.ROOT
P=ROOT/"runs/evidence-first-prepared-20261025-r1"
RUN=ROOT/"runs/evidence-first-live-20261025-r1"


def write(name,value):
    io.write(RUN/name,value)


def text_of(answer):
    return answer.get("text",answer.get("conclusion",answer.get("reasoning","")))


def main():
    manifest,plan=runner.verify(P);runner.gates(P)
    state=io.read(RUN/"progress.json");rows=state["rows"]
    requests=[io.strict_json(line) for line in (RUN/"requests.jsonl").read_text(encoding="utf-8").splitlines()]
    responses=[io.strict_json(line) for line in (RUN/"responses.jsonl").read_text(encoding="utf-8").splitlines()]
    assert state["status"]=="completed_with_quarantine" and state["attempts"]==72
    assert len(rows)==len(requests)==len(responses)==72 and len(list(RUN.glob("*.raw.txt")))==72
    assert [r["slot"] for r in rows]==list(range(1,73))
    assert all(r["retry"]==0 for r in requests)
    assert not state["unknown_usage"] and state["error"] is None
    assert [r["slot"] for r in rows if r["status"]=="quarantined"]==[63]
    assert all(r["status"]=="readable" for r in rows if r["slot"]!=63)
    firsts,deliveries={},{};costs=collections.defaultdict(lambda:dict(requests=0,input_tokens=0,output_tokens=0))
    integration_packets={};raw_final=[]
    for row,request,response in zip(rows,requests,responses):
        packet,blocked=runner.packet_for(P,row,firsts,deliveries)
        assert blocked is None
        expected=runner.make_request(row,packet)
        actual=io.read(RUN/"actual_requests"/f"{row['slot']:03d}.json")
        assert actual==expected
        assert request["payload"]["instructions"]==expected["instructions"]
        assert request["payload"]["text"]["format"]["schema"]==expected["schema"]
        assert set(expected["schema"]["required"])==set(expected["schema"]["properties"])
        assert request["payload"]["max_output_tokens"]==1536
        provider=response["response"]
        assert provider["status"]=="completed" and provider["error"] is None
        raw=(RUN/f"{row['slot']:03d}.raw.txt").read_text(encoding="utf-8")
        provider_text="".join(p["text"] for item in provider["output"] if item["type"]=="message"
                              for p in item["content"] if p["type"]=="output_text")
        assert raw==provider_text
        raw_obj=io.strict_json(raw)
        if row["slot"]==63:
            assert set(raw_obj)=={"choice","reasoning"}
            try:
                frontend.decode_integration(raw,packet)
            except ValueError as exc:
                assert "used_contributions" in str(exc)
            else:
                raise AssertionError("old contract must remain rejected")
        elif row["stage"]=="integrate":
            assert frontend.decode_integration(raw,packet)==row["answer"]
        else:
            assert frontend.decode(raw,row["stage"],packet)==row["answer"]
        if row["stage"]=="first":
            firsts[row["group"]]=row["answer"]
        elif row["stage"]=="second":
            deliveries.setdefault(f"{row['unit']}/{row['method']}",{})[row["member"]]=row["answer"]
        else:
            integration_packets[(row["task"],row["repeat"],row["method"])]=packet
            # Secondary forensics only: no missing field is filled and no old row changes.
            core=future_contract.decode(raw,packet)
            reference=io.read(P/f"OFFLINE_{row['task']}.json")["reference_choice"]
            raw_final.append(dict(slot=row["slot"],task=row["task"],repeat=row["repeat"],method=row["method"],
                                  frozen_status=row["status"],observed_raw_choice=core["choice"],reference=reference,
                                  raw_reference_match=core["choice"]==reference,
                                  raw_sha256=io.digest(RUN/f"{row['slot']:03d}.raw.txt")))
        cost=costs[row["method"]];cost["requests"]+=1
        for field in ("input_tokens","output_tokens"):
            cost[field]+=provider["usage"][field]
        assert provider["usage"]["output_tokens"]<=1536
    for field in ("input_tokens","output_tokens"):
        assert sum(r["response"]["usage"][field] for r in responses)==state[field]
    assert sum(r["estimated_input_count"] for r in requests)==state["reserved_estimated_input"]<=393216
    assert state["input_tokens"]<=393216 and state["output_tokens"]<=110592
    same_originals=[]
    for task in runner.TASKS:
        for repeat in (1,2):
            a=integration_packets[(task,repeat,"ordinary")]
            b=integration_packets[(task,repeat,"evidence_first")]
            same_originals.append(dict(task=task,repeat=repeat,equal=a["disclosed_evidence"]==b["disclosed_evidence"]))
            assert a["historical_work"]==b["historical_work"]
    assert all(row["equal"] for row in same_originals)
    scores=scorer.export(P,RUN)
    raw_counts={m:sum(r["raw_reference_match"] for r in raw_final if r["method"]==m) for m in frontend.METHODS}
    assert raw_counts==dict(ordinary=2,evidence_first=2)
    assert all(r["observed_raw_choice"]=="O1" for r in raw_final)
    byslot={r["slot"]:r for r in rows}
    trajectory=[
        dict(repeat=1,method="ordinary",first_slot=7,second_slot=8,final_slot=9,
             first_grant="absent",second_grant="absent",final_grant="not_explicit"),
        dict(repeat=1,method="evidence_first",first_slot=16,second_slot=17,final_slot=18,
             first_grant="explicit_and_task_linked",second_grant="explicit_in_comparison",
             final_grant="ambiguous_generic_fundraising_not_specific_grant"),
        dict(repeat=2,method="evidence_first",first_slot=25,second_slot=26,final_slot=27,
             first_grant="absent",second_grant="absent",final_grant="not_explicit"),
        dict(repeat=2,method="ordinary",first_slot=34,second_slot=35,final_slot=36,
             first_grant="absent",second_grant="rediscovered_and_task_linked",
             final_grant="explicit_in_comparison"),
    ]
    for entry in trajectory:
        for phase in ("first","second","final"):
            slot=entry[phase+"_slot"];text=text_of(byslot[slot]["answer"])
            entry[phase+"_text"]=text
            entry[phase+"_raw_sha256"]=io.digest(RUN/f"{slot:03d}.raw.txt")
    for slot in (16,17,35,36):
        assert "grant" in text_of(byslot[slot]["answer"]).lower()
    for slot in (7,8,9,18,25,26,27,34):
        assert "grant" not in text_of(byslot[slot]["answer"]).lower()
    assert "federal-grant evidence" in text_of(byslot[17]["answer"])
    assert "most strongly support Stevens" in text_of(byslot[25]["answer"])
    annotation_probes=[
        dict(slots=[14,15,23,24],observation="Candidate A3 accurately supplies Roberts teaching/research positives on both repeats; some ordinary outputs also do so. No stable final gain follows."),
        dict(slots=[36],observation="Ordinary final repeats 'two deanships' for Stevens, whereas P1 lists one business dean role and a department chair. Candidate finals do not make that exact role overstatement. A case-level rationale difference, not a general quality score."),
        dict(slots=[45,54,63,72],observation="All four hospital raw final explanations combine the current route and ICU constraints and select A; slot63's only contract defect is absent adoption metadata."),
    ]
    technical=dict(status="COMPLETED_WITH_ONE_QUARANTINED_TERMINAL_METADATA_OUTPUT",manifest_sha256=io.digest(P/"manifest.json"),
        planned=72,attempts=72,raw_responses=72,provider_completed=72,readable_under_frozen_contract=71,quarantined_slots=[63],
        retries=0,repairs=0,unknown_usage=False,input_tokens=state["input_tokens"],output_tokens=state["output_tokens"],
        estimated_input_tokens=state["reserved_estimated_input"],method_costs=dict(costs),requests_reconstructed_exactly=72,
        raw_text_matches_provider=72,paired_originals=same_originals,
        explanation="Provider omitted required used_contributions despite the sent required schema. Frozen parser quarantined it. No JSON damage, missing choice, missing reasoning or truncation; primary frozen score remains unknown for this slot.")
    write("TECHNICAL_AUDIT.json",technical)
    write("RAW_CHOICE_FORENSICS.json",dict(scope="SECONDARY_RAW_ANSWER_FORENSICS_NOT_A_RETROACTIVE_PRIMARY_SCORE",
          original_quarantine_preserved=True,essential_fields_available=8,raw_reference_matches=raw_counts,per_method_denominator=4,
          paired_choices_identical=4,raw_finals=raw_final))
    write("PROCESS_REVIEW.json",dict(annotation="Same-assistant posthoc nonblind targeted source-to-application review; no new global quality score.",
          grant_probe_trajectory=trajectory,other_case_observations=annotation_probes,
          conclusion="One candidate run surfaces and retains the known grant, but the other does not. Ordinary independently recovers and applies it in the second repeat. No stable candidate advantage in this batch.",
          limits=["Two already-used development tasks; no generalization estimate.",
                  "Explicit grant mention is not by itself correct application; the first candidate final is ambiguous, not silently counted as use or a factual contradiction.",
                  "Complete original evidence remains common and may compensate for summary differences; no causal isolation.",
                  "No initially correct W0, so no correct-answer retention or zero-harm claim."]))
    snapshot=RUN/"frozen_source"
    for rel,sha in manifest["code_sha256"].items():
        target=snapshot/rel;target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():
            shutil.copy2(ROOT/rel,target)
        assert io.digest(target)==sha
    io.write(snapshot/"SHA256.json",manifest["code_sha256"])
    write("FUTURE_INTERFACE_FIX.json",dict(status="COMPONENT_IMPLEMENTED_AND_LOCALLY_TESTED_NOT_ENABLED_IN_THIS_BATCH",
          component="tools/minimal_final_answer_contract.py",sha256=io.digest(ROOT/"tools/minimal_final_answer_contract.py"),
          mandatory_fields=["choice","reasoning"],adoption_measurement="Substantive evidence application review, not a self-reported list.",
          tests=4,test_seconds=0.005,new_model_requests=0))
    report=f"""# 先证据后对接：72次开发对照结果

审核日期2026-10-26，批次按原冻结名称20261025-r1保留。真实请求72次，未重试/补跑。

## 结论

本批没有显示新候选稳定优于普通贡献。4个配对单位的8份原始答案选项完全一致：005两组两遍均O1 Stevens（参考O2 Roberts），009均O1 Hospital A（参考O1）。原始选择核对为两组各2/4。这是次级原始答案审阅，不能抹掉冻结接口的一条隔离。

冻结完整接口结果：普通组4个最终单位中3份合规，1份参考命中、2份参考不匹配、1份技术unknown；候选组4份合规、2份参考命中、2份不匹配。不能拿1对2的合规命中数宣称候选提升——差别来自普通组槽63遗漏used_contributions。其原始choice=O1、完整理由均在且可读。SCORES.json保持原冻结口径；RAW_CHOICE_FORENSICS.json单独记录原始字段，未补写采纳列表、未改review.json。

## 知识链实际发生了什么

| 005遍次/方法 | A4首轮 | A4二轮 | 最终整合对拨款记录的处理 |
|---|---|---|---|
| 1 普通 | 未明确提取 | 未明确提取 | 未具体处理 |
| 1 候选 | 找到并联系任务 | 保留并用于候选比较 | 只泛称Roberts有筹款经历，无法确认具体使用了这项拨款 |
| 2 普通 | 未明确提取 | 自行补出并联系多样性/筹款标准 | 明确将数百万联邦拨款列入Roberts优点后比较 |
| 2 候选 | 仍遗漏 | 仍遗漏 | 仍未具体处理，筹款只具体讨论政治竞选 |

这保留一个局部正信号：候选第一次确实让已知漏项进入成员交付，并在看到W0后保留，没有全部失效。它没有重复成稳定优势：第二遍相同任务/资料下候选仍漏，普通组反而自行补出并在整合中使用。不能将“先独立”当作已解决选择困难，也不能从第一次成功宣称机制走通。

部分候选成员理由较完整，如A3两遍均讨论Roberts教学与科研生产率；普通组第二遍也能做到。普通最终槽36把Stevens写成two deanships，与P1一段院长经历加一段系主任经历不符，候选最终没有这一处夸大；这是可保留的案例差异，不据此创建事后总体质量分。

009两组原始最终答案均2/2，四份理由都将C氧气失效、B主路中断/缺床、A山口清通结合后选择A。尚无最终选择退化观察，不意味着全部中间推理正确。4个配对整合拿到的披露原件一致，不能将选择改善相对公共W0全归因于贡献文本。

## 对原因的修正

第二遍候选A4在完全未看到W0的首轮仍以Stevens为主并遗漏拨款（槽25）。因此，看到共同稿不是此类遗漏发生的必要条件。公共材料形成的偏好、任务相关性选择与底模推理等仍可能起作用；本批没有隔离它们的各自因果贡献。

普通组第二遍能补出并具体使用同一条资料，说明当前模型/普通流程并非完全没有这种能力；困难体现在触发与持续应用不稳定。只移动共同稿时机不足以稳定改善这一链条。本批仍只有一道多事实选择任务和一道直接约束任务，不能否定所有独立知识形成策略，也不支持继续直接扩张本版本。

## 运行审核

72次请求及原始响应齐全；71次符合冻结完整接口，1次末端元数据缺失隔离，0重试、0修复、0传输错误，usage完整。输入{state['input_tokens']:,}、输出{state['output_tokens']:,} tokens，估计输入{state['reserved_estimated_input']:,}，均在393216/110592总上限内。

72份实际请求由冻结原件和实际前序输出重建完全一致；W0按方法阶段可见，成员原件隔离、第二轮全本人原件和新增入口保留；原离线参考未进入请求。完整接口评分与次级原始字段核对分开。方法成本见TECHNICAL_AUDIT.json。

## 再次出现缺字段的原因与处理

服务端在槽63漏了schema已要求的used_contributions；响应status=completed、JSON有效、choice和reasoning完整，未达到输出1536上限。将required写进schema只能约束请求合同，不能保证服务永不违约。

此前把这种末端自报注释升级为整份答案的硬门槛，是过度收紧：它不决定答案能否评阅，也不构成真实采用证据。未来组件已简化为只要求choice和reasoning，采纳从实质推理审阅；不捏造空采纳列表。非法choice、缺核心理由、重复键和额外JSON仍拒绝，非核心额外注释单独保留。新组件4项本地测试通过，包括这份真实完整响应；尚未接入本批，也未建立新付费批次。

本批原隔离状态、评分、冻结源码与全部原始文本保留。工程处理详见engineering/TERMINAL_METADATA_FAILURE_20261026.md。

## 下一步决策

不自动扩跑本候选，不因为这一结果再增加固定角色或核查轮。把普通贡献作为当前可用基础，保留候选的个别提取/理由质量正信号。后续方法必须解释并针对“同一知识有时能被普通流程正确使用、有时连无共同稿阶段都忽略”的实际差异，避免继续把共同稿锚定当作已确定根因。

005按参考选择计分，但没有给各项岗位权重，选择不匹配不自动等于无争议逻辑错误。这个边界不妨碍我们定位拨款遗漏、职务夸大和元数据契约问题。本文过程判断为同助手事后非盲，未新增独立质量标注。
"""
    (RUN/"RESULTS.md").write_text(report,encoding="utf-8")
    io.write(P/"EXECUTION_STATUS.json",dict(status="COMPLETED_WITH_QUARANTINE_REVIEWED",live_model_requests=72,
              automatic_expansion=False,run=str(RUN.relative_to(ROOT)),report=str((RUN/"RESULTS.md").relative_to(ROOT)),
              manifest_sha256=io.digest(P/"manifest.json"),quarantined_slots=[63],raw_forensic_reference_matches=raw_counts))
    runner.verify(P)
    print(json.dumps(dict(status=state["status"],attempts=72,input_tokens=state["input_tokens"],output_tokens=state["output_tokens"],
                          frozen_scores=scores["by_method"],raw_forensic_matches=raw_counts,costs=dict(costs)),ensure_ascii=False))


if __name__=="__main__":
    main()
