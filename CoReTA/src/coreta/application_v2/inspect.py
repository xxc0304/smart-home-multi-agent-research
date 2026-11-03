"""Export trace evidence for human content inspection; never infer semantic success."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


QUESTIONS = {
    "gap_or_issue_valid": None,
    "reply_adds_usable_content": None,
    "receiver_uses_content_faithfully": None,
    "local_result_supported": None,
    "candidate_consistent_with_local_result": None,
    "remaining_uncertainty_preserved": None,
    "evidence_and_reason": None,
}


def collect(run):
    state = json.loads((run / "state.json").read_text(encoding="utf-8"))
    if state.get("protocol") != "coreta/application-v2":
        raise ValueError("Expected a v2 state")
    event_path = run / "events.jsonl"
    events = [json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines()] if event_path.exists() else []
    units = {u["ref"]: u for u in state["application_state"]["units"]}
    works = {w["ref"]: w for w in state["works"]}
    contributions = {c["ref"]: c for c in state["contributions"]}
    records = []
    for index, event in enumerate(events):
        if event["kind"] not in {"request", "review"}:
            continue
        is_reply = event["kind"] == "request"
        message = event["request"] if is_reply else event["review"]
        if is_reply:
            message = next((q for q in state["requests"] if q["ref"] == message["ref"]), message)
        app_ref = message.get("application_ref")
        if not is_reply:
            targets = [r for r in message["target_refs"] if r in units]
            app_ref = targets[0] if len(targets) == 1 else None
        following = events[index + 1:]
        receipt = next((e for e in following if e["kind"] == "reply_received" and e["request_ref"] == message["ref"]), None) if is_reply else event
        after_number = receipt["event_number"] if receipt else None
        action = next((e for e in following if e["kind"] == "apply" and after_number is not None
                       and e["event_number"] > after_number), None)
        before = next((e.get("work_ref") for e in reversed(events[:index]) if e["kind"] == "apply"), None)
        new_ref = action.get("application_change", {}).get("new_ref") if action else None
        records.append({
            "message_ref": message["ref"], "kind": "reply_handoff" if is_reply else "review",
            "source_event_number": event["event_number"], "message": message,
            "original_application": units.get(app_ref),
            "original_application_status_note": "Status is end-of-run metadata; payload is the original version.",
            "reply_received": receipt is not None if is_reply else None,
            "reply_contributions": [contributions[r] for r in message.get("reply_refs", []) if r in contributions],
            "following_apply_event": action, "following_application": units.get(new_ref),
            "replacement_application": units.get(new_ref) if action and app_ref is not None
                and action.get("application_change", {}).get("target") == app_ref else None,
            "candidate_before": works.get(before),
            "candidate_after": works.get(action.get("work_ref")) if action else None,
            "content_judgment": dict(QUESTIONS),
        })
    return {"kind": "human_content_inspection_unjudged", "protocol": state["protocol"],
            "source_run": str(run.resolve()), "automatic_semantic_success": None,
            "reference_answers_loaded": False, "records": records,
            "limits": "References and state transitions are evidence pointers, not proof of faithful use or correctness. No-defect final reviews may have no following APPLY."}


def export(run, output):
    if output.resolve().is_relative_to(run.resolve()):
        raise ValueError("Inspection output must be outside the source run")
    report = collect(run)
    output.mkdir(parents=True, exist_ok=False)
    (output / "evidence.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# 应用接续内容核验记录", "", "本记录尚未判定内容。不能把引用、状态转换或候选变化直接算作成功。",
             "", "完整原文、应用和候选前后见同目录 evidence.json。"]
    for row in report["records"]:
        original = row["original_application"] or {}
        replacement = row["replacement_application"] or {}
        lines += ["", f"## {row['message_ref']}（{row['kind']}，事件{row['source_event_number']}）", "",
                  f"- 原应用：{original.get('ref', '未定位唯一U')}；缺项：{original.get('missing')}",
                  f"- 原应用的修订版本：{replacement.get('ref', '无')}；回复资料：{', '.join(c['ref'] for c in row['reply_contributions']) or '无'}",
                  "", "请结合原始题目和可见材料填写，并写明依据：", "",
                  "| 核验项 | 判断与原文依据 |", "|---|---|",
                  "| 原缺项/纠错是否成立 | 未判定 |", "| 回复是否增加可用内容 | 未判定 |",
                  "| 接收者具体如何使用，是否忠实 | 未判定 |", "| 局部结果是否有支持 | 未判定 |",
                  "| 最终候选是否与局部结果一致；不变是否合理 | 未判定 |",
                  "| 未解决部分是否如实保留 | 未判定 |"]
    (output / "REVIEW.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="A new separate inspection directory")
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(args.run.resolve()):
        parser.error("Inspection output must be outside the source run")
    try:
        report = export(args.run, args.output)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps({"inspection": str(args.output), "records": len(report["records"]),
                      "semantic_judgments": "unjudged", "network_requests": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
