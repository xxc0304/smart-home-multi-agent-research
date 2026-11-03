"""Offline integrity, paired scoring, and process summary for the 152-call pilot."""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

import run_hiddenbench_local_contribution as runner
import local_judgment_frontend as io

ROOT = Path(__file__).resolve().parents[1]
PREPARED = ROOT / "runs/hb-local-contribution-prepared-20261025-r1"
OUT = ROOT / "runs/hb-local-contribution-live-20261025-r1"
TASKS = [f"hb-local-dev-{n:03d}" for n in (5, 9, 12, 23)]
METHODS = ("ordinary", "local_question")


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(name: str, value):
    (OUT / name).write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def output_text(response: dict) -> str:
    return "".join(
        part["text"]
        for item in response.get("output", [])
        if item.get("type") == "message"
        for part in item.get("content", [])
        if part.get("type") == "output_text" and isinstance(part.get("text"), str)
    )


def main():
    manifest, plan, config = runner.verify(PREPARED)
    runner.gates(PREPARED)
    progress = read(OUT / "progress.json")
    review = read(OUT / "review.json")
    rows = progress["rows"]
    roster = plan["schedule"]
    requests = [json.loads(x) for x in (OUT / "requests.jsonl").read_text(encoding="utf-8").splitlines()]
    responses = [json.loads(x) for x in (OUT / "responses.jsonl").read_text(encoding="utf-8").splitlines()]
    row_by_slot = {r["slot"]: r for r in rows}

    assert progress["mode"] == "live" and progress["status"] == "completed"
    assert progress["attempts"] == len(roster) == len(rows) == len(requests) == len(responses) == 152
    assert len(review["rows"]) == 152 and [r["slot"] for r in review["rows"]] == list(range(1, 153))
    assert [r["slot"] for r in rows] == list(range(1, 153))
    assert all(r["status"] == "readable" for r in rows)
    assert not progress["unknown_usage"] and progress["error"] is None
    assert len(list(OUT.glob("*.raw.txt"))) == 152
    assert all(req["retry"] == 0 and req["attempt"] == i for i, req in enumerate(requests, 1))
    assert all(resp["response"]["status"] == "completed" and resp["response"]["error"] is None for resp in responses)

    stage_counts = collections.Counter(r["stage"] for r in rows)
    method_counts = collections.Counter(r["method"] for r in rows)
    assert stage_counts == {"initial": 8, "first": 64, "second": 64, "integrate": 16}
    assert method_counts == {"ordinary": 72, "local_question": 72, "common": 8}

    # Replay the actual dynamic packet construction from the frozen materials and
    # the actual preceding model outputs, without contacting a model.
    common, firsts, deliveries = {}, {}, {}
    request_reconstruction = 0
    paired_member_packets = 0
    schema_contract_gaps = []
    for expected_row in roster:
        row = row_by_slot[expected_row["slot"]]
        assert {k: row[k] for k in expected_row} == expected_row
        packet, blocked = runner.packet_for(PREPARED, row, common, firsts, deliveries)
        assert blocked is None
        expected_request = runner.make_request(row, packet)
        actual_request = read(OUT / "actual_requests" / f"{row['slot']:03d}.json")
        assert actual_request == expected_request
        if row["stage"] in ("initial", "integrate"):
            required = set(actual_request["schema"].get("required", []))
            missing_required = sorted({"choice", "used_contributions"} - required)
            if missing_required:
                schema_contract_gaps.append(dict(slot=row["slot"], stage=row["stage"], missing_required=missing_required))
        log_request = requests[row["slot"] - 1]
        payload = log_request["payload"]
        assert payload["instructions"] == expected_request["instructions"]
        assert payload["max_output_tokens"] == expected_request["max_output_tokens"] == 1536
        assert payload["text"]["format"]["schema"] == expected_request["schema"]
        assert payload["model"] == config["model"]
        request_reconstruction += 1

        response = responses[row["slot"] - 1]["response"]
        text = output_text(response)
        raw_path = OUT / f"{row['slot']:03d}.raw.txt"
        raw = raw_path.read_text(encoding="utf-8")
        assert raw == text and json.loads(raw) is not None
        usage = response["usage"]
        assert all(type(usage.get(k)) is int and usage[k] >= 0 for k in ("input_tokens", "output_tokens"))
        assert usage["output_tokens"] <= 1536

        answer = row["answer"]
        if row["stage"] == "initial":
            common[row["unit"]] = runner.draft_from(answer)
        elif row["stage"] == "first":
            firsts[row["group"]] = answer
            if answer["status"] == "pass":
                deliveries.setdefault(f"{row['unit']}/{row['method']}", {})[row["member"]] = dict(
                    conclusion=answer["text"], status="abstain",
                    scope="Explicit first-stage pass; no local conclusion asserted.",
                    missing=[], evidence=answer["evidence"], annotation_issues=answer["annotation_issues"])
        elif row["stage"] == "second":
            deliveries.setdefault(f"{row['unit']}/{row['method']}", {})[row["member"]] = answer

    # The paired local packets must have the same contents; only the method prompt differs.
    for task in TASKS:
        for repeat in (1, 2):
            first_rows = [r for r in roster if r["task"] == task and r["repeat"] == repeat and r["stage"] == "first"]
            for member in runner.MEMBERS:
                packets = []
                for r in first_rows:
                    if r["member"] == member:
                        actual = read(OUT / "actual_requests" / f"{r['slot']:03d}.json")
                        packets.append(io.strict_json(actual["instructions"].split("PACKET=", 1)[1]))
                assert len(packets) == 2 and packets[0] == packets[1]
                paired_member_packets += 1

    assert paired_member_packets == 32
    for field in ("input_tokens", "output_tokens"):
        assert sum(r["response"]["usage"][field] for r in responses) == progress[field]
    estimated_input = sum(r["estimated_input_count"] for r in requests)
    reserved_output = sum(r["payload"]["max_output_tokens"] for r in requests)
    assert estimated_input == progress["reserved_estimated_input"] <= 786432
    assert reserved_output == progress["reserved_output"] <= 233472
    assert progress["input_tokens"] <= 786432 and progress["output_tokens"] <= 233472

    costs = collections.defaultdict(lambda: dict(requests=0, input_tokens=0, output_tokens=0))
    for row, response in zip(rows, responses):
        c = costs[row["method"]]
        c["requests"] += 1
        c["input_tokens"] += response["response"]["usage"]["input_tokens"]
        c["output_tokens"] += response["response"]["usage"]["output_tokens"]

    offline = {task: read(PREPARED / f"OFFLINE_{task}.json") for task in TASKS}
    answer_rows = {(r["task"], r["repeat"], r["method"], r["stage"]): r for r in rows}
    initial_score = {m: 0 for m in METHODS}
    final_score = {m: 0 for m in METHODS}
    task_scores = {}
    paired = []
    for task in TASKS:
        ref = offline[task]["reference_choice"]
        name = offline[task]["reference_name"]
        task_scores[task] = {"reference_choice": ref, "reference_name": name}
        for method in METHODS:
            correct, initial_correct = 0, 0
            task_scores[task][method] = {"initial": [], "final": []}
            for repeat in (1, 2):
                initial = answer_rows[(task, repeat, "common", "initial")]["answer"]["choice"]
                final = answer_rows[(task, repeat, method, "integrate")]["answer"]["choice"]
                initial_correct += int(initial == ref)
                correct += int(final == ref)
                task_scores[task][method]["initial"].append(initial)
                task_scores[task][method]["final"].append(final)
                paired.append(dict(task=task, repeat=repeat, method=method, initial=initial,
                                   final=final, reference=ref, initial_correct=initial == ref,
                                   final_correct=final == ref, changed=initial != final))
            initial_score[method] += initial_correct
            final_score[method] += correct
            task_scores[task][method]["initial_correct"] = initial_correct
            task_scores[task][method]["final_correct"] = correct

    paired_choices = []
    same_final_choices = 0
    for task in TASKS:
        for repeat in (1, 2):
            ordinary = answer_rows[(task, repeat, "ordinary", "integrate")]["answer"]["choice"]
            question = answer_rows[(task, repeat, "local_question", "integrate")]["answer"]["choice"]
            same = ordinary == question
            same_final_choices += int(same)
            paired_choices.append(dict(task=task, repeat=repeat, ordinary=ordinary,
                                       local_question=question, same=same))

    private_disclosure = []
    final_member_private_citation = 0
    for row in rows:
        if row["stage"] != "second":
            continue
        own_ref = row["member"] + ".S1"
        cited = any(e["source"] == own_ref for e in row["answer"]["evidence"])
        final_member_private_citation += int(cited)
        private_disclosure.append(dict(slot=row["slot"], task=row["task"], repeat=row["repeat"],
                                       method=row["method"], member=row["member"], own_private_source_cited=cited))

    integrations = []
    for row in rows:
        if row["stage"] != "integrate":
            continue
        actual = read(OUT / "actual_requests" / f"{row['slot']:03d}.json")
        packet = io.strict_json(actual["instructions"].split("PACKET=", 1)[1])
        local_refs = sorted(e["ref"] for e in packet["disclosed_evidence"] if e["ref"].endswith(".S1"))
        answer = row["answer"]
        integrations.append(dict(slot=row["slot"], task=row["task"], repeat=row["repeat"], method=row["method"],
                                 choice=answer["choice"], used_contributions=answer["used_contributions"],
                                 disclosed_private_refs=local_refs, annotation_issues=answer["annotation_issues"]))

    annotation_issues = [dict(slot=r["slot"], stage=r["stage"], task=r["task"], method=r["method"],
                              issues=r["answer"]["annotation_issues"])
                         for r in rows if r["answer"]["annotation_issues"]]
    assert len(schema_contract_gaps) == 24
    assert len(annotation_issues) == 4
    assert all(issue["field"] == "used_contributions" and issue["issue"] == "missing"
               for row in annotation_issues for issue in row["issues"])
    local_questions = [r for r in rows if r["method"] == "local_question" and r["stage"] == "first"]
    ordinary_firsts = [r for r in rows if r["method"] == "ordinary" and r["stage"] == "first"]
    qmark_count = sum("?" in r["answer"]["text"] for r in local_questions)
    ordinary_qmark_count = sum("?" in r["answer"]["text"] for r in ordinary_firsts)

    technical = dict(
        status="PASS_WITH_NONFATAL_SCHEMA_CONTRACT_GAP", manifest_sha256=io.digest(PREPARED / "manifest.json"),
        authorization=read(PREPARED / "AUTHORIZATION.json")["user_authorization_text"],
        planned_and_completed_requests=152, raw_outputs=152, parsed_responses=152,
        statuses=dict(collections.Counter(r["status"] for r in rows)), stages=dict(stage_counts), methods=dict(method_counts),
        retries=0, unreadable=0, quarantined=0, transport_or_provider_errors=0, unknown_usage=False,
        request_reconstruction=f"{request_reconstruction}/152 exact from frozen packets plus actual prior outputs",
        paired_member_input_packets=f"{paired_member_packets}/32 exact match; method prompt is the assigned difference",
        raw_text_matches_provider_output=True, json_outputs_valid=152,
        output_cap_per_request=1536, max_observed_output_tokens=max(r["response"]["usage"]["output_tokens"] for r in responses),
        estimated_input_tokens=estimated_input, actual_input_tokens=progress["input_tokens"], input_cap=786432,
        reserved_output_tokens=reserved_output, actual_output_tokens=progress["output_tokens"], output_cap=233472,
        per_method_usage=dict(costs), common_initial_requests=8,
        schema_contract_gaps=dict(team_output_requests_with_choice_and_used_contributions_not_required=f"{len(schema_contract_gaps)}/24",
                                  missing_from_required_fields=["choice", "used_contributions"], affected_request_slots=schema_contract_gaps,
                                  prompt_requires_used_contributions=True, decoder_records_but_does_not_reject_missing_field=True,
                                  preflight_missed_because_mock_fixtures_always_supplied_fields=True),
        annotation_issues=annotation_issues,
        semantic_limits=[
            "Technical parsing does not establish factual correctness or semantic usefulness.",
            "used_contributions is a model self-report; evidence disclosure and actual reasoning were separately retained.",
            "The exact packet reconstruction verifies no offline reference labels entered model inputs.",
            "A nonfatal output-contract gap remains: the initial and integration prompts expect choice and used_contributions, but the sent JSON schemas required only reasoning. Four outputs omitted used_contributions. This does not invalidate the parsed choices or reasoning, but the pre-run format audit failed to catch the mismatch.",
        ],
    )
    score_data = dict(scope="Exact match to dataset-provided reference; not a proof of unique normative answer.",
                      reference_kind={t: offline[t]["reference_kind"] for t in TASKS},
                      initial_common_public_only_correct="0/8", by_task=task_scores,
                      final_correct={m: f"{final_score[m]}/8" for m in METHODS},
                      initial_correct_by_arm={m: f"{initial_score[m]}/8" for m in METHODS},
                      paired_final_choices=paired_choices, identical_choice_pairs=f"{same_final_choices}/8",
                      transitions="Both methods change the public-only initial choice to the reference on both repeats of 009, 012, and 023; both retain O1 on 005, whose reference is O2.",
                      no_initial_correct_public_answer=True)
    process = dict(
        final_member_outputs_citing_own_private_source=f"{final_member_private_citation}/64",
        integrations=integrations,
        model_reported_used_contribution_coverage="See each integration; this field is an optional self-report, not an adoption ground truth.",
        local_question_first_outputs_with_literal_question_mark=f"{qmark_count}/32",
        ordinary_first_outputs_with_literal_question_mark=f"{ordinary_qmark_count}/32",
        annotation_issues=annotation_issues,
        interpretation=[
            "All four members were independently run from isolated packets, and the actual disclosed evidence was assembled for an integrator. This is a genuine distributed-information, multi-agent setting, but it does not include member-to-member replies, reassignment, or a feedback loop.",
            "The two arms used the same team integration prompt and same task evidence; the only intended difference was the first-stage member prompt. Final choices match in every paired instance, so this batch shows no final-choice advantage for local_question over ordinary contribution.",
            "The prompt-schema mismatch affects the self-reported used_contributions field: two public-only initial outputs and two integration outputs omit it. This weakens that secondary adoption indicator, not the extracted final choices or their reasoning. A stricter versioned runner and regression check were added after the live run.",
            "Both arms improved over the public-only W0 choice on 009, 012, and 023. Since they received additional private evidence, made many more calls, and had integration, that contrast shows that the distributed evidence was usable in these cases; it does not isolate coordination as the cause or compare against a cost-matched one-agent/full-information control.",
            "005 is a reference mismatch, but the benchmark supplies no numerical weights or unique-maximizer proof. Treat 6/8 as reference agreement, and report the O1-vs-O2 disagreement with its criterion ambiguity rather than presenting it as a clean binary reasoning failure.",
        ],
    )
    write("TECHNICAL_AUDIT.json", technical)
    write("SCORES.json", score_data)
    write("PROCESS_REVIEW.json", process)

    table = "\n".join(
        f"| {task[-3:]} | {offline[task]['reference_name']} ({offline[task]['reference_choice']}) | "
        f"{task_scores[task]['ordinary']['final_correct']}/2 | {task_scores[task]['local_question']['final_correct']}/2 | "
        f"{', '.join(task_scores[task]['ordinary']['final'])} |"
        for task in TASKS
    )
    cost_lines = "\n".join(
        f"| {method} | {costs[method]['requests']} | {costs[method]['input_tokens']:,} | {costs[method]['output_tokens']:,} |"
        for method in METHODS
    )
    report = f'''# 四任务协作对照结果（2026-10-25）

## 结果

两种方法的最终答案都是 **6/8**，8个配对结果的选项完全一致。两组都把共同初答在009、012、023上的错误选择改成了数据集参考答案；005两次都保留O1，而数据集参考是O2。故这批有“分散资料进入整合后可纠正初答”的正面观察，**没有发现“先提出局部问题再求解”优于普通贡献的最终答案增益**。

| 任务 | 数据集参考 | 普通贡献 | 局部提问 | 普通组最终选项 |
|---|---|---:|---:|---|
{table}

共同公共初答为0/8。这是公共信息起点，不是一个调用数、信息量或计算预算匹配的协作基线。最终6/8不能全归因于协调方式，因为最终团队另外拿到了四份私有资料并经过多次生成与整合。

## 这次实验究竟比较了什么

每道题有4个隔离资料成员、共同公共初答、成员两步交付和一个整合者；每题重复两遍。普通组成员首轮可直接提出证据、计算、问题或条件判断；局部提问组首轮要求先提出一个由自己资料支持的局部问题，再由同一成员在第二轮处理。第二轮和最终整合对两组相同。

它是有真实分散信息的多Agent流程，但没有成员之间相互回复、根据他人问题改派、或整合后的check-back。因此不能把它称为普通集中讨论与完整CoReTA架构的对照；它识别的是首轮“普通贡献 vs 自主提出局部问题”这一个提示差异。

## 局部知识有没有进入团队答案

64/64份最终成员交付都引用了各自私有原件；每个整合请求均由宿主按实际交付重建，只披露成员真正引用的原文，没有给整合者未披露的私有资料。009、012、023的两组整合理由都使用了推动改答的跨成员事实：医院题结合C氧气系统失效、B道路/床位约束和A山口已清通；疏散题结合Green Valley的游客例外、Red Lake唯一道路封闭和Blueberry Ridge电力/车辆可达问题；宴会题结合Lakeview断路、图书馆禁外烩及Grand Oak电话预订例外。

005上，整合者两组都提到募款证据被高估并引用成员提供的修正，但仍选Stevens。原基准没有给岗位标准权重，也没有证明Roberts是唯一可能选择。因此能确定的是“未匹配数据集标注”，不能将其直接说成无争议的推理错误。它仍提示我们：即使贡献被传递并引用，贡献对最终排序的影响也可能有限。

4份输出漏了`used_contributions`自报字段：两份公共初答（009重复1、012重复2）和两份整合（012重复1局部提问组、023重复2普通组）。它们都通过JSON解析，选择与理由仍在；因此不是JSON损坏或服务调用失败，但确实暴露了**提示与Schema不一致**：提示要求返回该字段，实际Schema却只要求`reasoning`，解码器也把缺字段记为注释问题而继续接受。它不改变本批主要选项分数，却使该字段不能作可靠的采用率指标。

这项准备缺口本应在启动前审核出来，但没有。原因已定位：本地模拟输出总是带有该字段，测试只验证Schema自身合法，没有断言prompt要求的字段都在`required`中，也没有注入“JSON合法、漏必需语义字段”的案例。为不改写本批冻结代码，我保留了运行时8个源码文件的精确快照，并新增版本化的严格运行器，要求`choice`、`reasoning`、`used_contributions`必填，缺失/非法字段会进入隔离并阻断依赖；相应回归检查已通过。

操纵检查显示，局部提问组32份首轮有31份写出显式问句，普通贡献组是0/32；因此两种首轮行为确实被拉开。局部提问组仍有不少文本在提出问题前后给出有根据的局部判断，所以这是“以问题组织贡献”，不是纯粹只提问。关键是，这种明确的问题化没有带来最终选项增益；它是否提高了贡献质量或理由清晰度，尚未用独立盲评量化。

## 运行与成本审核

152/152请求完成；0重试、0不可读、0隔离、0传输错误。所有原始响应均与服务端文本一致并通过JSON解析；但存在上面说明的字段Schema契约缺口，不能把本批称为“完全没有格式/协议问题”。冻结输入和实际前序模型输出逐槽重建一致；32对成员首轮看到完全相同的任务/公共材料/本人私有材料，第二轮仅含本人先前输出及本人资料。输入累计实际312,850 tokens、保守预估{estimated_input:,} tokens；输出累计51,143 tokens。两组调用量都是72，成本如下：

| 方法 | 请求数 | 输入tokens | 输出tokens |
|---|---:|---:|---:|
{cost_lines}

另有8次两组共用的公共初答调用（输入/输出分别计入完整运行总量）。详见`TECHNICAL_AUDIT.json`。本批没有无效JSON或服务端schema拒绝，但有4个合法JSON漏掉提示要求、Schema未强制的字段；这属于接口契约问题，已定位并修正未来运行版本。

## 对主线的判断

这批与主线**相关**：它确实让四个各持局部资料的Agent把知识交给共同解答，且三类任务中整合成功改正公共初答。结果支持继续研究“分散知识怎样被交付和应用”这条问题线。

但它没有说明自主提问是解决缺口的有效机制：普通贡献产生了完全相同的选项结果。也没有证明成员互相协作比一个看到全部资料的单Agent更好，因为本批没有那个对照。不能据此宣称完整架构提升，也不应只凭这次平局就否定成员局部知识的价值。

## 下一步

先停止这轮扩跑，保留这批结果。下一项有区分力的问题不是再加协议，而是核对现有日志中哪种差异可能影响最终答案：成员是否在首轮识别并交付了独特局部事实、两种提示是否改变了事实被披露/整合的程度、整合者是否对某一条知识作了实质性推理。然后用新的、真正信息量足够且答案有明确依据的任务做小规模复核；若目标是证明多Agent相对单Agent的增量，应设置同信息、同模型调用/token预算的全信息单Agent对照。先前的开发结果也应保留，不能把本批4题当成独立留出测试。
'''
    (OUT / "RESULTS.md").write_text(report, encoding="utf-8")

    status_path = PREPARED / "EXECUTION_STATUS.json"
    status = read(status_path) if status_path.exists() else {}
    status.update(status="COMPLETED_REVIEWED_WITH_NONFATAL_SCHEMA_CONTRACT_GAP", live_model_requests=152, automatic_expansion=False,
                  run=str(OUT.relative_to(ROOT)), report=str((OUT / "RESULTS.md").relative_to(ROOT)),
                  technical_audit="PASS_WITH_NONFATAL_SCHEMA_CONTRACT_GAP", final_reference_match={m: f"{final_score[m]}/8" for m in METHODS},
                  postrun_fix="tools/run_hiddenbench_local_contribution_v2.py requires and decodes all team output fields; local regression check passed")
    write_status = json.dumps(status, ensure_ascii=False, indent=2) + "\n"
    status_path.write_text(write_status, encoding="utf-8")
    print(json.dumps({"technical": "PASS_WITH_NONFATAL_SCHEMA_CONTRACT_GAP", "score": score_data["final_correct"],
                      "paired_identical": same_final_choices, "costs": dict(costs),
                      "private_citations": f"{final_member_private_citation}/64",
                      "annotation_issues": len(annotation_issues)}, ensure_ascii=False))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
