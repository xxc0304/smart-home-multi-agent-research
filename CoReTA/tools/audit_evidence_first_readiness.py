"""Final offline readiness audit; only writes unfrozen review/status metadata."""
import json
from pathlib import Path
import evidence_first_frontend as frontend
import export_evidence_first_pilot as scoring
import local_judgment_frontend as io
import run_evidence_first_pilot as runner

ROOT=io.ROOT
P=ROOT/"runs/evidence-first-prepared-20261025-r1"


def main():
    _,plan=runner.verify(P);sha=io.digest(P/"manifest.json")
    pre=io.read(P/"PREFLIGHT.json")
    assert pre["status"]=="passed" and pre["manifest_sha256"]==sha
    records={}
    for name in ("history_replay","stress_replay"):
        run=P/name;state=io.read(run/"progress.json")
        assert state["mode"]=="local_fixture" and state["status"]=="completed" and state["attempts"]==72
        assert len(list(run.glob("*.raw.txt")))==72
        assert all(r["status"]=="readable" and not r["answer"]["annotation_issues"] for r in state["rows"])
        logs=[io.strict_json(line) for line in (run/"requests.jsonl").read_text(encoding="utf-8").splitlines()]
        assert all(log["retry"]==0 for log in logs)
        firsts,deliveries={},{}
        visibility={"ordinary_first":0,"ordinary_second":0,"evidence_first_first":0,"evidence_first_second":0}
        for row in state["rows"]:
            packet,blocked=runner.packet_for(P,row,firsts,deliveries)
            assert blocked is None
            actual=io.read(run/"actual_requests"/f"{row['slot']:03d}.json")
            assert actual==runner.make_request(row,packet)
            assert set(actual["schema"]["required"])==set(actual["schema"]["properties"])
            if row["stage"]!="integrate":
                key=row["method"]+"_"+row["stage"]
                visibility[key]+=1
                assert [s["ref"] for s in packet["own_sources"]]==[row["member"]+".S1"]
                should_have_draft=(row["method"]=="ordinary")==(row["stage"]=="first")
                assert ("historical_work" in packet)==should_have_draft
                if should_have_draft:
                    assert packet["historical_work"]==io.read(P/"drafts"/row["task"]/f"r{row['repeat']}.json")
                if row["stage"]=="second":
                    assert packet["earlier_work"]==firsts[row["group"]]["text"]
                    base=io.read(P/"contexts"/row["task"]/f"{row['member']}.json")
                    assert packet["own_sources"]==base["own_sources"]
            if row["stage"]=="first":
                firsts[row["group"]]=row["answer"]
            elif row["stage"]=="second":
                deliveries.setdefault(f"{row['unit']}/{row['method']}",{})[row["member"]]=row["answer"]
        assert all(value==16 for value in visibility.values())
        exported=scoring.export(P,run)
        assert exported["scope"]=="TECHNICAL_FIXTURE_NOT_EXPERIMENTAL_RESULTS" and exported["paid_live_requests"]==0
        records[name]=dict(visibility=visibility,reconstructed_requests=72,annotation_issues=0,
                           source_scope="All member originals retained; no source IDs from peers.",
                           estimated_input_tokens=sum(log["estimated_input_count"] for log in logs),
                           max_input_tokens=max(log["estimated_input_count"] for log in logs))
    for task in runner.TASKS:
        for repeat in (1,2):
            assert io.read(P/"drafts"/task/f"r{repeat}.json")==io.read(runner.HISTORY/"common_drafts"/task/f"r{repeat}.json")
    tests=ROOT/"runs/evidence-first-test-evidence-20261025.txt"
    final_tests=ROOT/"runs/evidence-first-final-check-20261025.txt"
    assert "Ran 7 tests" in tests.read_text(encoding="utf-8-sig") and "OK" in tests.read_text(encoding="utf-8-sig")
    assert "Ran 3 tests" in final_tests.read_text(encoding="utf-8-sig") and "OK" in final_tests.read_text(encoding="utf-8-sig")
    evidence=dict(status="PASS",manifest_sha256=sha,live_model_requests=0,replays=records,
                  frozen_drafts_identical_to_archives=4,
                  full_suite=dict(tests=7,seconds=20.509,log=str(tests.relative_to(ROOT)),sha256=io.digest(tests)),
                  affected_followup=dict(tests=3,seconds=12.988,log=str(final_tests.relative_to(ROOT)),sha256=io.digest(final_tests)),
                  test_source_sha256=io.digest(ROOT/"tests/test_evidence_first_pilot.py"),
                  checked_boundaries=["missing required fields at every stage","null/invalid choice","unknown/foreign source",
                    "wrong array and field types","duplicate JSON keys","extra fields/extra JSON","single branch quarantine",
                    "pass continues to second view","newly noticed sources in second view","two unreadable outputs",
                    "transport/unknown usage","actual and estimated budget bounds","frozen tampering/old authorization rejected",
                    "all 72 slots on interruption; unknown scores not wrong","full historical and synthetic extended load"])
    io.write(P/"READINESS_EVIDENCE.json",evidence)
    io.write(P/"TEST_EVIDENCE.json",dict(manifest_sha256=sha,full_suite=evidence["full_suite"],
                                      affected_followup=evidence["affected_followup"],test_source_sha256=evidence["test_source_sha256"]))
    io.write(P/"EXPERIMENT_REVIEW.json",dict(science="PASS",readiness="PASS",technical_launch="RUN_ALLOWED",
                manifest_sha256=sha,independent_review=False,
                research_scope="Two-task development diagnostic of a bundled evidence-formation/application mechanism, not pure W0 causality or broad accuracy superiority.",
                authorization="NOT_AUTHORIZED",live_model_requests=0))
    io.write(P/"AUTHORIZATION.json",dict(authorized=False,status="AWAITING_SPECIFIC_BATCH_AUTHORIZATION",
                max_requests=72,max_output_tokens=110592,max_input_tokens=393216,
                destination="https://api.deepseek.com/responses",manifest_sha256=sha,
                user_authorization_text=None,automatic_expansion=False))
    io.write(P/"EXECUTION_STATUS.json",dict(status="PREPARED_REVIEWED_NOT_AUTHORIZED",model_requests=0,manifest_sha256=sha,
                proposed_live_output="runs/evidence-first-live-20261025-r1",automatic_expansion=False))
    report=f"""# 证据先行开发小试：实验前审核

2026-10-25。冻结目录evidence-first-prepared-20261025-r1，manifest SHA256：{sha}。

## 研究意义：PASS（有限开发诊断）

固定005/009各2遍、原生4成员、两组各36调用，共72。005检验多条资料选择，009检验直接约束组合的退化；仅一道多事实选择任务，不能支持广泛稳定收益。四份W0来自上一批真实公共初答，完整相同且无新付费初答；两题均为已用开发资料，不冒充留出。

普通组先见W0后继续本人评议；候选先形成本地含义、第二轮再见W0对接。第二轮两组都可新增原件支持的内容、撤回错误、保留多条互补贡献。两组首次pass均继续二轮，不因候选晚见稿而不公平减少普通组调用。第一轮去掉两组都不使用的target_ids，未限制普通组自然问题、条件推理或完整偏好。组合处理有效性与纯锚定因果区分。

没有随机可信度/标准权重，没有人工正确问题或Roberts拨款提示。完整本人原件、公共材料和既有普通整合政策保留，宿主只按合法句柄呈现实际披露原文，不填知识。原件已披露仍遗漏的现象需要实际应用来检验，引用数不等于采用。

评分在SCORING_AND_PLAN.md冻结：最终每组4单位参考命中，正确局部含义、正确对接、最终实际使用分别审查；005无数值权重，不造加权金标。记录新增错误、首轮到二轮丢失、技术unknown和成本。四份W0均未命中参考，不能报告正确初答保留率或零损害。重复和成员单位不作独立任务显著性证据。单助手事后非盲语义审核声明保留。

## 准备完备性：PASS

7项完整本地测试通过（20.509秒）；提示中修正“不得只选一个对象”可能误迫单事实任务扩写后，相关全流程、pass、新授权/真实回放3项复核通过（12.988秒）。

72槽完整真实历史回放通过。首轮仅移除旧target_ids元数据，正文、status、source_ids完整保留；二轮/整合保留完整历史输出。候选首轮旧输出可能讨论旧稿，这是接口技术夹具，不能说已观察新候选行为。

另72槽扩展负载回放通过：完整原始文本不删减，复制其完整句子扩展到单次1536 tokens以内，明确是合成负载，不是新语义结果。正常最大输入{records['history_replay']['max_input_tokens']}/32768、累计估算{records['history_replay']['estimated_input_tokens']}/393216；扩展最大{records['stress_replay']['max_input_tokens']}/32768、累计估算{records['stress_replay']['estimated_input_tokens']}/393216。所测输入有余量，不保证所有任意输出组合的绝对上界。

两份回放各72次请求由冻结资料和真实前序输出重新组包逐槽完全一致，所有阶段schema的properties均列入required；0来源/元数据注释异常。32个首轮及32个二轮按方法检查W0可见性，每方法阶段16项；候选第一轮无W0、第二轮有W0，普通组反向。本人全原件保留，二轮来源不是首轮引用白名单。4份缓存W0与历史逐对象一致，无评分字段进入请求。

缺字段、错误类型、非法choice、null、无权引用、重复键、额外字段/JSON、单条隔离及依赖阻断、两连续失败停止、传输与未知usage、输入/输出预算、错误授权/冻结篡改等均有覆盖。独立离线导出已验证中断保留72槽/8个最终名单、technical_unknown不记错，并明确模拟结果不是实验成绩。

## 预算与总体结论

最多72次，输出1536/次及110592总上限，输入32768/次及393216累计保守估计/实际上限。deepseek-flash、temperature0.7、reasoning none，官方https://api.deepseek.com/responses。零重试/格式修复/续跑/自动扩跑。单条不可读隔离并阻断依赖；两连续不可读或传输/未知usage/预算/冻结故障停止。

总体技术结论RUN_ALLOWED；当前NOT_AUTHORIZED / NOT_STARTED，真实API请求0。旧152次授权已完成，仓库AGENTS.md和实验章程要求本批具体数据及目的地的适用授权。设计与技术审核通过不保证服务永不违约，也不预先保证方法有效。
"""
    (P/"EXPERIMENT_REVIEW.md").write_text(report,encoding="utf-8")
    runner.verify(P)
    try:
        runner.gates(P)
    except ValueError as exc:
        assert "authorization" in str(exc)
    else:
        raise AssertionError("unauthorized batch unexpectedly allowed")
    print(json.dumps(dict(science="PASS",readiness="PASS",manifest_sha256=sha,live_model_requests=0,
                          replays={name:dict(max_input=data["max_input_tokens"],total_input=data["estimated_input_tokens"])
                                   for name,data in records.items()},authorization="NOT_AUTHORIZED")))


if __name__=="__main__":
    main()
