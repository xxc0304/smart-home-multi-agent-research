"""Generate an inventory of physical run folders without treating them as experiments."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
OUTPUT = Path(__file__).resolve().parent / "run-index.md"
LIVE_RESULTS_OUTPUT = Path(__file__).resolve().parent / "live-results-index.md"


def role(name: str) -> str:
    lowered = name.casefold()
    if "draft" in lowered:
        return "draft"
    if "prepared" in lowered:
        return "prepared"
    if "offline" in lowered:
        return "offline"
    if "live" in lowered:
        return "live"
    return "other / auxiliary"


def main() -> None:
    folders = sorted((path for path in RUNS.iterdir() if path.is_dir()), key=lambda p: p.name.casefold())
    counts = Counter(role(path.name) for path in folders)
    labels = {
        "live": "名字含 live；是否完成看 progress/results 文件",
        "prepared": "名字含 prepared；通常是待运行冻结材料",
        "offline": "名字含 offline；离线分析或校验材料",
        "draft": "名字含 draft；草稿或候选材料",
        "other / auxiliary": "其他；可能是评分、检查、数据、授权或历史记录",
    }
    lines = [
        "# runs/ 目录索引",
        "",
        f"当前共列出 **{len(folders)} 个物理目录**。此数字是文件夹数量，不是独立实验数；同一批次可能有 prepared、live、check、scores 等多个目录，也可能有重复、未完成或辅助材料。",
        "",
        "分类按目录名自动推断，只用于导航。每项的实际状态、样本数、结果和授权以目录内的 `manifest.json`、`progress.json`、结果报告及审核记录为准。",
        "",
        "## 分类统计",
        "",
        "| 类别 | 数量 | 含义 |",
        "|---|---:|---|",
    ]
    for key in ("live", "prepared", "offline", "draft", "other / auxiliary"):
        lines.append(f"| {key} | {counts[key]} | {labels[key]} |")
    for key in ("live", "prepared", "offline", "draft", "other / auxiliary"):
        group = [path for path in folders if role(path.name) == key]
        lines.extend(["", f"## {key} ({len(group)})", "", "| 目录 | 可直接打开的记录 |", "|---|---|"])
        for folder in group:
            name = folder.name
            evidence = []
            for filename, label in (
                ("RESULTS.md", "results"),
                ("progress.json", "progress"),
                ("manifest.json", "manifest"),
                ("EXPERIMENT_REVIEW.md", "review"),
            ):
                if (folder / filename).is_file():
                    evidence.append(f"[{label}](../runs/{name}/{filename})")
            if not evidence:
                evidence = [f"[目录](../runs/{name}/)"]
            lines.append(f"| [`{name}`](../runs/{name}/) | {', '.join(evidence)} |")
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    live_reports = [
        folder for folder in folders
        if "live" in folder.name.casefold() and (folder / "RESULTS.md").is_file()
    ]
    result_lines = [
        "# Live-named run result reports",
        "",
        f"本页列出目录名含 `live` 且有 `RESULTS.md` 的 **{len(live_reports)} 个目录**。它们包含已完成和中断/部分批次；此清单只证明有结果报告，不代表批次通过、完整或可合并。",
        "",
        "按批次目录名称排序。每项报告中的冻结口径、分母、技术状态和解释边界优先；目录名中的 `live` 不表示当前仍在运行。",
        "",
        "| 日期 | 批次目录 | 报告标题 | 原始报告 | 运行状态记录 |",
        "|---|---|---|---|---|",
    ]
    for folder in live_reports:
        match = re.search(r"(20\d{2})(\d{2})(\d{2})", folder.name)
        date = "-".join(match.groups()) if match else "未标注"
        title = next(
            (line[2:].strip() for line in (folder / "RESULTS.md").read_text(encoding="utf-8", errors="replace").splitlines() if line.startswith("# ")),
            "RESULTS.md",
        )
        title = title.replace("|", "\\|")
        progress = f"[progress](../runs/{folder.name}/progress.json)" if (folder / "progress.json").is_file() else "—"
        result_lines.append(
            f"| {date} | [`{folder.name}`](../runs/{folder.name}/) | {title} | "
            f"[RESULTS.md](../runs/{folder.name}/RESULTS.md) | {progress} |"
        )
    LIVE_RESULTS_OUTPUT.write_text("\n".join(result_lines) + "\n", encoding="utf-8")
    print(
        f"Indexed {len(folders)} folders and {len(live_reports)} live-named reports; "
        f"categories={dict(counts)}"
    )


if __name__ == "__main__":
    main()
