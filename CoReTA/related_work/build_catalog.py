"""Build the consolidated CoReTA related-work catalog from local ledgers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
LEDGERS = ROOT / "ledgers"
OUTPUT = ROOT / "catalog.json"
MARKDOWN_OUTPUT = ROOT / "catalog.md"
PAPERS = ROOT / "papers"


def source_kind(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    if host in {"arxiv.org", "aclanthology.org", "proceedings.mlr.press", "proceedings.neurips.cc", "papers.nips.cc", "proceedings.iclr.cc", "iclr.cc", "openreview.net", "dl.acm.org", "ieeexplore.ieee.org", "link.springer.com", "doi.org"}:
        return "paper_or_proceedings"
    if host == "github.com":
        return "repository_or_code"
    if urlparse(url).path.lower().endswith(".pdf"):
        return "paper_or_document"
    return "other_source"


def local_full_text(url: str) -> dict[str, str]:
    acl_match = re.search(r"aclanthology\.org/(\d{4}\.[a-z0-9-]+\.\d+)(?:/|\.pdf)?$", url)
    if acl_match:
        folder = PAPERS / f"acl-{acl_match.group(1)}"
        if (folder / "paper.pdf").is_file():
            return {
                "full_text_status": "archived",
                "local_full_text": f"papers/{folder.name}/paper.pdf",
                "archived_version": "ACL Anthology official",
            }
    match = re.search(r"arxiv\.org/(?:abs|html|pdf|src)/(\d{4}\.\d{4,5})(?:v\d+)?", url)
    if not match or not PAPERS.exists():
        return {"full_text_status": "link_only"}
    paper_id = match.group(1)
    folders = [
        folder for folder in PAPERS.glob(f"arxiv-{paper_id}v*")
        if (folder / "paper.pdf").is_file()
    ]
    if not folders:
        return {"full_text_status": "link_only"}
    folders.sort(
        key=lambda folder: int(re.search(r"v(\d+)$", folder.name).group(1))
        if re.search(r"v(\d+)$", folder.name)
        else -1
    )
    folder = folders[-1]
    version = re.search(r"v\d+$", folder.name)
    return {
        "full_text_status": "archived",
        "local_full_text": f"papers/{folder.name}/paper.pdf",
        "archived_version": version.group(0) if version else "unknown",
    }


def read_ledger(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    records: list[dict[str, str]] = []

    if path.suffix.lower() == ".json":
        payload = json.loads(text)
        sources = payload.get("sources", []) if isinstance(payload, dict) else []
        for item in sources:
            if not isinstance(item, dict) or not item.get("url"):
                continue
            records.append(
                {
                    "title": str(item.get("title") or item["url"]),
                    "url": str(item["url"]),
                    "scope": str(item.get("read_scope") or item.get("scope") or item.get("boundary") or ""),
                }
            )
        return records

    for label, url in re.findall(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", text):
        label = re.sub(r"\s+", " ", label).strip()
        url = url.rstrip(".,;:")
        records.append({"title": label or url, "url": url, "scope": ""})

    linked_urls = {record["url"] for record in records}
    for url in re.findall(r"https?://[^\s)\]>]+", text):
        url = url.rstrip(".,;:")
        if url not in linked_urls:
            records.append({"title": url, "url": url, "scope": ""})
            linked_urls.add(url)
    return records


def main() -> None:
    grouped: dict[str, dict] = {}
    for ledger in sorted(LEDGERS.iterdir()):
        if ledger.suffix.lower() not in {".md", ".json"}:
            continue
        for record in read_ledger(ledger):
            entry = grouped.setdefault(
                record["url"],
                {
                    "title": record["title"],
                    "url": record["url"],
                    "kind": source_kind(record["url"]),
                    "mentioned_in": [],
                },
            )
            entry.update(local_full_text(record["url"]))
            if len(record["title"]) > len(entry["title"]):
                entry["title"] = record["title"]
            mention = {"ledger": ledger.name}
            if record.get("scope"):
                mention["scope"] = record["scope"]
            if mention not in entry["mentioned_in"]:
                entry["mentioned_in"].append(mention)

    payload = {
        "generated_from": "related_work/ledgers/",
        "generated_on": "2026-10-28",
        "scope": "Consolidated links from prior CoReTA literature and benchmark ledgers. The arXiv full texts available locally are marked archived; other sources may remain link-only.",
        "references": sorted(grouped.values(), key=lambda item: (item["kind"], item["title"].casefold(), item["url"])),
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# CoReTA 相关工作来源目录",
        "",
        f"从 `ledgers/` 汇总 `{len(payload['references'])}` 个去重 URL；此目录合并已有讨论中的论文、会议页、数据/代码来源和其他研究材料。`archived` 表示本地存在全文，`link_only` 表示目前只有来源链接。",
        "",
        "| 类型 | 来源 | 全文状态 | 本地文件 | 讨论出处 |",
        "|---|---|---|---|---|",
    ]
    for item in payload["references"]:
        title = item["title"].replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")
        ledgers = ", ".join(f"`{mention['ledger']}`" for mention in item["mentioned_in"])
        local = f"[`paper.pdf`]({item['local_full_text']})" if item.get("local_full_text") else "—"
        lines.append(f"| {item['kind']} | [{title}]({item['url']}) | {item.get('full_text_status', 'link_only')} | {local} | {ledgers} |")
    MARKDOWN_OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(payload['references'])} unique source URLs to {OUTPUT} and {MARKDOWN_OUTPUT}")


if __name__ == "__main__":
    main()
