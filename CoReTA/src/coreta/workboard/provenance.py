"""Describe current source access using visible metadata, never hidden originals."""
from collections import defaultdict


SOURCE_GUIDANCE = (
    "SOURCE_ACCESS distinguishes access from reported provenance. Only TASK and your SELF_MATERIALS "
    "are directly read originals. Public offers/candidates are reports you can use, but their mentions, "
    "support excerpts, or historical declared_sources do not give you direct access to those originals. "
    "For peer-reported knowledge, cite the public O/W carrier you actually used in declared_sources "
    "(or support.ref), not its inaccessible original ID. Explain the indirect basis and any limits in "
    "use_record/work_text; do not call it personally verified from originals. A provider can verify its "
    "own originals and report that check without the recipient gaining original access. "
    "SOURCE_ACCESS.reported_originals is a navigation aid derived from peer metadata, not verification "
    "of a claim or proof that a carrier supports it. Only REFERENCE_INDEX IDs are legal citations. "
)


def describe_sources(packet):
    """Mutate only access metadata; retain all original content and reference IDs."""
    direct = {"T", *(m["ref"] for m in packet["SELF_MATERIALS"])}
    available = {r["ref"] for r in packet["REFERENCE_INDEX"]}
    direct &= available
    public = available - direct
    reported = defaultdict(set)
    for offer in packet.get("PUBLIC_EVIDENCE", []):
        if offer["ref"] in public:
            for support in offer["support"]:
                if support["ref"] not in available:
                    reported[support["ref"]].add(offer["ref"])
    works = {w["id"]: w for w in packet.get("CANDIDATES", [])}
    for key in ("CURRENT_WORK", "BEFORE", "AFTER", "FALLBACK", "FINAL_PROPOSAL"):
        w = packet.get(key)
        if w and "declared_sources" in w:
            works[w["id"]] = w
    for ref, work in works.items():
        if ref in public:
            for source in work["declared_sources"]:
                if source not in available:
                    reported[source].add(ref)
    for row in packet["REFERENCE_INDEX"]:
        row["access"] = "direct_original" if row["ref"] in direct else "public_report"
    packet["SOURCE_ACCESS"] = {
        "direct_original_refs": sorted(direct),
        "public_report_refs": sorted(public),
        "reported_originals": [{"reported_ref": ref, "via_public_refs": sorted(carriers),
                                 "status": "peer_metadata_not_verified"}
                                for ref, carriers in sorted(reported.items())],
    }
    if any(w.get("source_declaration_status") == "not_collected" for w in works.values()):
        packet["SOURCE_ACCESS"]["uncollected_declaration_meaning"] = (
            "not_collected means this stage did not ask for source declarations; an empty list does not "
            "mean the author used no materials. Collected declarations are claims, not verification."
        )
    return packet
