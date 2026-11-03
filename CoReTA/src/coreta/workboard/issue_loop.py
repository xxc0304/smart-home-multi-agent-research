"""Opt-in, version-bound issue feedback. Model reports never certify correctness."""
import copy

from .contracts import TEXT, obj, handles
from .gateway import defaults
from .grounded import GroundContracts, GroundPrompts, GroundRunner
from .runtime import Runner
from ..handoff.gateway import write_json
from ..schemas import ProtocolError


VARIANT = "ground_issue_loop_v2"
CHECK_STAGES = {"CHECK_USE", "CHECK_EFFECT", "FINAL_CHECK_USE", "FINAL_CHECK_EFFECT"}
CHOICE_STAGES = {"CHOOSE", "FINAL_CHOOSE"}
ACCESS_GUIDANCE = (
    "CHECKER_ACCESS belongs to you. WORK_AUTHOR_ACCESS belongs to each named work's "
    "author: never project your own access onto that author. Author availability is "
    "allocation metadata, not proof of actual reading or a grant of source access to you. "
    "APPLICATION_ACTOR_ACCESS identifies the editor making the present application, "
    "which can differ from a reused work's author. Check APPLICATION_SOURCE_REFS against "
    "that actor's situation; check a work's first-person access statements against its author. "
)
WORK_VIEW_GUIDANCE = (
    "CANDIDATES holds canonical full works. CURRENT_WORK/BEFORE/AFTER/FINAL_PROPOSAL/"
    "FALLBACK may be handles {id, content_in:CANDIDATES}; resolve them by id to the full "
    "candidate before inspecting any content or difference. Handles do not omit work evidence. "
)


def deduplicate_work_views(packet):
    """Keep every full candidate once; replace repeated top-level copies by handles."""
    canonical = {w['id'] for w in packet.get('CANDIDATES', [])}
    for key in ('CURRENT_WORK', 'BEFORE', 'AFTER', 'FINAL_PROPOSAL', 'FALLBACK'):
        work = packet.get(key)
        if work and work['id'] in canonical:
            packet[key] = {'id': work['id'], 'content_in': 'CANDIDATES'}
    return packet


def attach_access_context(packet, application_actor, originals_by_member):
    """Only attach allocation metadata; keep private content and legal citations intact."""
    checker = packet["SELF"]["agent_id"]
    packet["CHECKER_ACCESS"] = {"agent_id": checker, **copy.deepcopy(packet["SOURCE_ACCESS"])}
    works = {packet[key]["id"]: packet[key]
             for key in ("BEFORE", "AFTER", "FINAL_PROPOSAL", "FALLBACK") if packet.get(key)}
    packet["WORK_AUTHOR_ACCESS"] = {
        ref: {"author": work["author"],
              "available_original_refs": sorted(originals_by_member[work["author"]])}
        for ref, work in works.items()}
    packet["APPLICATION_ACTOR_ACCESS"] = {"agent_id": application_actor,
        "available_original_refs": sorted(originals_by_member[application_actor])}
    return packet


def settings(member_count, legacy):
    value = defaults(member_count, legacy)
    value["max_output_tokens"].update(ground=3072, choose=2048, final_choose=2048)
    value["budget_status"] = "issue_loop_development_not_frozen"
    return value


class IssueContracts(GroundContracts):
    def schema(self, stage, packet):
        schema = super().schema(stage, packet)
        refs = {r["ref"] for r in packet["REFERENCE_INDEX"]}
        evidence = {"type": "array", "items": handles(refs), "uniqueItems": True,
                    "minItems": 1}
        if stage in CHECK_STAGES:
            schema["properties"]["issues"] = {"type": "array", "items": obj(
                concern=TEXT, location=TEXT,
                kind={"enum": ["source_use", "reasoning", "delivery"]},
                evidence_refs=evidence, consequence=TEXT)}
            schema["properties"]["rechecks"] = obj(**{
                row["issue_id"]: obj(status={"enum": ["resolved", "persists", "unable"]},
                    reason=TEXT, evidence_refs=evidence)
                for row in packet.get("ISSUES_TO_RECHECK", [])})
            schema["required"] += ["issues", "rechecks"]
        if stage in CHOICE_STAGES:
            schema["properties"]["issue_dispositions"] = obj(**{
                ref: obj(disposition={"enum": ["accept", "reject", "unresolved"]}, reason=TEXT)
                for ref in packet["REQUIRED_ISSUE_IDS"]})
            schema["required"].append("issue_dispositions")
        return schema

    @staticmethod
    def validate_action(stage, value):
        GroundContracts.validate_action(stage, value)
        if stage in CHECK_STAGES:
            statuses = {row["status"] for row in value["rechecks"].values()}
            has_issue = bool(value["issues"]) or "persists" in statuses
            if ((value["finding"] == "issue") != has_issue
                    or (value["finding"] == "no_issue_found" and "unable" in statuses)):
                raise ProtocolError("INVALID_ACTION", "finding must reflect both new issues and outstanding rechecks")


class IssuePrompts(GroundPrompts):
    def render(self, stage, packet, schema):
        extra = ""
        if stage in CHECK_STAGES:
            extra = ACCESS_GUIDANCE + (
                "Separate factual mistakes from debatable weighting of task criteria. For each real "
                "problem supply a concrete issue, location, evidence refs and consequence. Recheck "
                "each ISSUES_TO_RECHECK item against AFTER (or FINAL_PROPOSAL); explain resolved, "
                "persists or unable. Resolved may mean the original allegation was mistaken, with "
                "evidence. Do not duplicate a rechecked problem as a new issue. finding=issue if "
                "there is a new issue or any persists recheck; if only unable rechecks remain, "
                "use finding=unable. A source owner's report can verify transmission from its own material; "
                "it does not independently establish the underlying fact. Do not invent issues. ")
        elif stage in CHOICE_STAGES:
            extra = (
                "Respond to every REQUIRED_ISSUE_IDS item for the version you select. accept means "
                "the problem is valid and remains to be repaired; reject requires concrete reasons "
                "that address its evidence; unresolved retains the doubt. You cannot mark a problem "
                "resolved by preference or by choosing a well-formed deliverable. Evaluate substantive "
                "consequences for the task, including evidence weighting, separately from citation "
                "bookkeeping. You may retain a best-effort version with explicit unresolved issues. ")
        elif stage in {"TRY", "FINALIZE"}:
            extra = (
                "Use ISSUE_LEDGER to revisit unresolved problems in the actual work; an earlier "
                "accept/reject is fallible, not proof. Repair concrete accepted problems when possible "
                "and show the resulting change in the work and use_record. For evidence-weighting "
                "disputes, explain how the evidence affects the task criteria and final comparison; "
                "adding an uncertainty phrase alone may not repair the argument. ")
        return WORK_VIEW_GUIDANCE + extra + super().render(stage, packet, schema)


class IssueRunner(GroundRunner):
    def __init__(self, *args, **kwargs):
        self.issue_ledger = []
        super().__init__(*args, **kwargs)
        if not isinstance(self.gateway.contracts, IssueContracts) or not isinstance(self.gateway.prompts, IssuePrompts):
            raise ProtocolError("INPUT_ERROR", "IssueRunner requires IssueContracts and IssuePrompts")

    @staticmethod
    def assessment(row, work_id):
        reviews = [r for r in row["rechecks"] if r["work_id"] == work_id]
        statuses = {r["status"] for r in reviews}
        if statuses == {"resolved"}:
            return "model_reported_resolved"
        if "resolved" in statuses and "persists" in statuses:
            return "conflicting_reviews"
        return "open_or_uncertain"

    def visible_issues(self, work_id):
        return [{**copy.deepcopy(row), "assessment_for_version": self.assessment(row, work_id)}
                for row in self.issue_ledger
                if self.assessment(row, work_id) != "model_reported_resolved"]

    def ground_packet(self, offer):
        packet = super().ground_packet(offer)
        packet["METHOD_VARIANT"] = VARIANT
        return deduplicate_work_views(packet)

    def packet(self, member, stage, **extra):
        packet = super().packet(member, stage, **extra)
        packet["METHOD_VARIANT"] = VARIANT
        if stage != "INITIAL":
            packet["ISSUE_LEDGER"] = self.visible_issues(self.board.current)
        if stage in CHECK_STAGES:
            attach_access_context(packet, self.editor, {
                agent: {"T", *(m["ref"] for m in self.packets.member(agent)["SELF_MATERIALS"])}
                for agent in self.agents})
            packet["ISSUES_TO_RECHECK"] = self.visible_issues(packet["AFTER"]["id"])
            packet["ISSUE_LEDGER"] = copy.deepcopy(packet["ISSUES_TO_RECHECK"])
        if stage in CHOICE_STAGES:
            # Include every not-yet-closed issue, including fresh checks and editorial rejections.
            packet["REQUIRED_ISSUE_IDS"] = sorted({row["issue_id"] for row in self.issue_ledger
                if any(self.assessment(row, ref) != "model_reported_resolved"
                       for ref in packet["CHOICES"])})
            packet["ISSUE_LEDGER"] = [{**copy.deepcopy(row), "assessments_by_choice": {
                ref: self.assessment(row, ref) for ref in packet["CHOICES"]}}
                for row in self.issue_ledger if row["issue_id"] in packet["REQUIRED_ISSUE_IDS"]]
        return deduplicate_work_views(packet)

    def event(self, kind, **value):
        if kind == "check_observation":
            check = value["check"]
            check["check_id"] = f"R{len(self.checks)}"
            for issue_id, review in check["rechecks"].items():
                row = next(row for row in self.issue_ledger if row["issue_id"] == issue_id)
                row["rechecks"].append({"check_id": check["check_id"], "member": check["member"],
                    "stage": check["stage"], "work_id": check["after"], **copy.deepcopy(review)})
            for index, issue in enumerate(check["issues"], 1):
                issue["issue_id"] = f"{check['check_id']}.I{index}"
                self.issue_ledger.append({"issue_id": issue["issue_id"],
                    "raised_on": check["after"], "checker": check["member"],
                    "check_id": check["check_id"], "detail": copy.deepcopy(issue),
                    "dispositions": [], "rechecks": []})
            self.checks[-1] = copy.deepcopy(check)
        if kind in {"offer_adopted", "offer_not_adopted", "selection_unchanged", "final_selection"}:
            decision = value["decision"]
            for issue_id, disposition in decision["issue_dispositions"].items():
                row = next(row for row in self.issue_ledger if row["issue_id"] == issue_id)
                row["dispositions"].append({"cycle": self.cycle, "work_id": decision["candidate_id"],
                    "stage": "FINAL_CHOOSE" if kind == "final_selection" else "CHOOSE",
                    **copy.deepcopy(disposition)})
        super().event(kind, **value)

    def save_state(self):
        Runner.save_state(self)
        write_json(self.journal.root / "issue_ledger.json", {
            "variant": VARIANT, "issues": self.issue_ledger, "truth_status": "not_certified"})
        write_json(self.journal.root / "method_variant.json", {
            "variant": VARIANT, "visibility": "full_public_not_blind",
            "ordinary_cycle": "observe_peers,ground,try,check_use,choose",
            "finalization": "two_checks_with_issue_rechecks", "truth_status": "not_certified"})

    def run(self):
        result = Runner.run(self)
        result["method_variant"] = VARIANT
        result["issue_summary"] = {"raised": len(self.issue_ledger),
            "selected_version_open_or_uncertain": len(self.visible_issues(result["selected_work_id"])),
            "semantic_resolution": "model_reports_only_not_ground_truth"}
        write_json(self.journal.root / "result.json", result)
        return result
