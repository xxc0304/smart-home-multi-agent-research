"""Assemble this literature investigation's checked records and reading index."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parent
records = []
for branch in ("ANCHOR", "METHODS", "EVALUATION", "EXPERTISE"):
    for record in json.loads((ROOT / f"{branch}.json").read_text(encoding="utf-8")):
        record["reading_record"] = f"{branch}.md"
        records.append(record)
by_id = {record["id"]: record for record in records}
assert len(by_id) == len(records), "Duplicate record ID"
required = {"id", "title", "authors", "year", "venue", "version", "url", "read_scope", "problem", "mechanism", "findings", "conditions", "limits", "gap_kind", "relevance", "verification"}
for record in records:
    assert required <= record.keys(), (record["id"], required - record.keys())

report_path = ROOT / "REPORT.md"
report = report_path.read_text(encoding="utf-8")
marker = re.compile(r"\{\{cite:([^}]+)\}\}")
order = list(dict.fromkeys(marker.findall(report)))
if order:
    missing = set(order) - by_id.keys()
    assert not missing, missing
    order += [record["id"] for record in records if record["id"] not in order]
    ref_map = {paper_id: index + 1 for index, paper_id in enumerate(order)}
    report = marker.sub(lambda match: f"[{ref_map[match[1]]}]({by_id[match[1]]['url']})", report)
    bibliography = []
    for paper_id in order:
        record = by_id[paper_id]
        authors = record["authors"]
        name = ", ".join(authors[:3]) + (", et al." if len(authors) > 3 else "")
        bibliography.append(f"[{ref_map[paper_id]}] {name}, \"{record['title']},\" {record['venue']}, {record['year']}. 阅读版本：{record['version']}。")
    report = report.replace("{{REFERENCES}}", "\n\n".join(bibliography))
    report_path.write_text(report, encoding="utf-8")
    (ROOT / "reference_map.json").write_text(json.dumps(ref_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
else:
    ref_map = json.loads((ROOT / "reference_map.json").read_text(encoding="utf-8"))

def cell(value):
    if isinstance(value, list):
        value = "；".join(value)
    return str(value).replace("|", "\\|").replace("\n", " ").strip()

ordered = sorted(records, key=lambda record: ref_map[record["id"]])
for record in ordered:
    record["reference_number"] = ref_map[record["id"]]
payload = {"date": "2026-10-28", "brief": "BRIEF.md", "core_paper_count": len(ordered), "reading_scope": "Relevant method/result/limitation sections, not every word of every full paper", "records": ordered}
(ROOT / "CORPUS.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

lines = ["# 逐篇证据矩阵：问题、操作、已解部分与剩余条件", "", f"本轮 {len(ordered)} 篇核心记录。编号与 REPORT.md 一致。观察到的失败、未验证条件与机制推断在 gap_kind 中分开；‘未验证’不表示方法无效。详细元数据、条件与阅读范围见 CORPUS.json 和四份分视角记录。", "", "| 工作与阅读依据 | 研究问题 | 实际操作 | 已验证的进展 | 剩余问题与证据边界 |", "|---|---|---|---|---|"]
for record in ordered:
    label = f"[{record['reference_number']}] [{record['title']}]({record['url']})；{record['version']}；[阅读记录]({record['reading_record']})"
    lines.append("| " + " | ".join(cell(value) for value in [label, record["problem"], record["mechanism"], record["findings"], record["limits"]]) + " |")
lines += ["", "## 逐篇阅读范围", "", "| 编号 | 实际核读范围 | 条件 | 缺口性质 | 核验记录 |", "|---|---|---|---|---|"]
for record in ordered:
    lines.append("| " + " | ".join(cell(value) for value in [record["reference_number"], record["read_scope"], record["conditions"], record["gap_kind"], record["verification"]]) + " |")
(ROOT / "PAPER_MATRIX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

sources = []
seen = set()
for record in ordered:
    for field in ("url", "metadata_url"):
        url = record.get(field)
        if not url or url in seen:
            continue
        seen.add(url)
        sources.append({"title": record["title"], "url": url, "read_scope": record["read_scope"] if field == "url" else "元数据/正式发表记录核验；技术阅读范围见主来源", "version": record["version"], "record_id": record["id"]})
sources.append({"title": "DEAR: NeurIPS 2026 official accepted-title list", "url": "https://neurips.cc/Downloads/2026", "read_scope": "精确题名与poster链接核验，不据列表声称已读正式论文PDF"})
ledger = ROOT.parents[1] / "related_work" / "ledgers" / "expertise-literature-survey-2026-10-28.json"
ledger.write_text(json.dumps({"date": "2026-10-28", "report": "research/expertise-literature-survey-20261028/REPORT.md", "sources": sources}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

assert "{{cite:" not in report and "{{REFERENCES}}" not in report
assert set(ref_map) == set(by_id)
print(f"Assembled {len(ordered)} core records; {len(sources)} source URLs in survey ledger")
