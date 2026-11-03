"""D0 variant; shared solving and closure machinery remain in workboard-v3."""
import copy
import json

from ..workboard.runtime import Runner as BaseRunner
from ..workboard.provenance import describe_sources
from ..handoff.gateway import write_json
from . import PROTOCOL


class Runner(BaseRunner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.focus_history = []

    def active_focus(self):
        return next((f for f in reversed(self.focus_history) if f["status"] == "pending"), None)

    def save_state(self):
        super().save_state()
        path = self.journal.root / "state.json"
        state = json.loads(path.read_text(encoding="utf-8"))
        state.update(protocol=PROTOCOL, focus_history=copy.deepcopy(self.focus_history),
                     active_focus_id=(self.active_focus() or {}).get("id"))
        write_json(path, state)

    def packet(self, member, stage, **extra):
        p = super().packet(member, stage, **extra)
        if stage == "INITIAL":
            return p
        p["FOCUS"] = copy.deepcopy(self.active_focus())
        p["FOCUS_HISTORY"] = copy.deepcopy(self.focus_history)
        focus_ids = {f["id"] for f in self.focus_history}
        focus_works = {f[key] for f in self.focus_history
                       for key in ("origin_work", "selected_work", "base_work")}
        focus_works.update(f["target"].split(":", 1)[0] for f in self.focus_history)
        focus_works.update(ref.split(":", 1)[0] for f in self.focus_history for ref in f["refs"])
        p["FOCUS_FEEDBACK"] = copy.deepcopy([row for row in self.feedback
            if row.get("focus_id") in focus_ids or row.get("after") in focus_works
            or row.get("offer", {}).get("responds_to") in focus_ids])
        # Only actual, already-public work is carried forward. No original private material is read.
        related = focus_works & self.board.ids()
        works = {w["id"]: w for w in p.get("CANDIDATES", [])}
        works.update({ref: self.board.get(ref) for ref in sorted(related) if ref in self.board.ids()})
        if works:
            p["CANDIDATES"] = list(works.values())
            known = {r["ref"] for r in p["REFERENCE_INDEX"]}
            p["REFERENCE_INDEX"] += [{"ref": ref, "kind": "public_focus_work"}
                                      for ref in works if ref not in known]
        targets = {"whole_goal"}
        for key in ("CURRENT_WORK", "BEFORE", "AFTER", "FALLBACK", "FINAL_PROPOSAL"):
            if p.get(key):
                works[p[key]["id"]] = p[key]
        for work in works.values():
            targets.add(work["id"])
            targets.update(work.get("locations", {}))
        p["FOCUS_TARGETS"] = sorted(targets)
        if stage == "TRY":
            p["APPLICATION_FEEDBACK"] = copy.deepcopy(self.feedback)
        return describe_sources(p)

    def apply_disposition(self, choice, focus_id):
        disposition = choice.get("focus_disposition")
        if disposition is not None:
            # The packet's dynamic schema allows only its active input focus.
            focus = next(f for f in self.focus_history if f["id"] == focus_id)
            focus["status"] = disposition["status"]
            focus["dispositions"].append({"cycle": self.cycle, "selected_work": choice["candidate_id"],
                                           **copy.deepcopy(disposition)})
            self.event("focus_disposition", disposition=disposition, selected_work=choice["candidate_id"])

    def record_choice(self, choice, base, trial, focus_id):
        self.apply_disposition(choice, focus_id)
        check = choice["next_check"]
        if check is not None:
            focus = {"id": f"Q{len(self.focus_history) + 1}", "author": self.editor,
                     "created_cycle": self.cycle, "origin_work": trial,
                     "selected_work": choice["candidate_id"], "base_work": base,
                     "status": "pending", "responses": [], "applications": [], "dispositions": [],
                     **copy.deepcopy(check)}
            self.focus_history.append(focus)
            self.event("focus_opened", focus=focus)

    def collaborate(self):
        # Same v3 call order, rotation and budget; only public focus follow-through is added.
        self.stop_reason = "cycle_limit"
        for cycle in range(1, len(self.agents)):
            if self.gateway.remaining < len(self.agents) + 3 + 4:
                self.stop_reason = "cycle_budget_reserved_for_closure"
                break
            self.cycle = cycle
            base = self.board.current
            snapshots = [(m, self.packet(m, "OBSERVE")) for m in self.agents if m != self.editor]
            batch = []
            for member, packet in snapshots:
                value = self.gateway.call("OBSERVE", member, packet)
                for previous in self.feedback:
                    if previous["kind"] == "unable_to_apply" and previous["offer"]["author"] == member:
                        previous["reason_delivered_to_provider"] = True
                if value["action"] == "pass":
                    self.event("pass", member=member, base_version=base)
                    continue
                offer = {"ref": f"O{len(self.offers) + 1}", "author": member,
                         "base_version": base, **value["offer"]}
                self.offers.append(copy.deepcopy(offer))
                batch.append(offer)
                self.event("offer_proposed", offer=offer)
            self.published.extend(copy.deepcopy(batch))
            for offer in batch:
                if offer["responds_to"]:
                    focus = next(f for f in self.focus_history if f["id"] == offer["responds_to"])
                    focus["responses"].append(offer["ref"])
                    self.event("focus_response", focus_id=focus["id"], offer_ref=offer["ref"])
            if not batch:
                self.stop_reason = "all_pass"
                break
            selected = self.choose_offer(batch)
            for offer in batch:
                self.event("offer_selected" if offer["ref"] == selected["ref"] else "offer_untried",
                           offer_ref=offer["ref"], base_version=base)
            focus_id = (self.active_focus() or {}).get("id")
            value = self.gateway.call("TRY", self.editor, self.packet(self.editor, "TRY", TARGET_OFFER=selected))
            if value["action"] == "unable":
                row = {"kind": "unable_to_apply", "offer": selected, "reason": value["reason"],
                       "base_version": base, "reason_delivered_to_provider": False, "focus_id": focus_id}
                self.feedback.append(row)
                self.event("offer_not_applied", feedback=row)
                continue
            trial = self.materialize(value, base=base)
            self.event("trial_created", offer_ref=selected["ref"], before=base, after=trial,
                       use_record=value["use_record"], declared_sources=value["declared_sources"])
            linked = {ref for ref in (focus_id, selected["responds_to"]) if ref}
            for focus in self.focus_history:
                if focus["id"] in linked:
                    # This is a navigation link, not a claim that the focus was actually resolved.
                    focus["applications"].append({"cycle": cycle, "offer_ref": selected["ref"],
                                                   "before": base, "after": trial,
                                                   "relation": ("selected_response" if selected["responds_to"] == focus["id"]
                                                                else "active_context_only")})
            checks = self.run_checks(selected["author"], base, trial, offer=selected,
                                     use_record=value["use_record"], declared_sources=value["declared_sources"])
            choice = self.gateway.call("CHOOSE", self.editor, self.packet(self.editor, "CHOOSE",
                BEFORE=self.board.get(base), AFTER=self.board.get(trial), CHECKS=checks,
                CHOICES=list(dict.fromkeys([base, trial]))))
            self.board.promote(choice["candidate_id"])
            self.record_choice(choice, base, trial, focus_id)
            self.feedback.append({"kind": "application_feedback", "offer": selected,
                "before": base, "after": trial, "use_record": value["use_record"],
                "checks": checks, "decision": choice, "focus_id": focus_id})
            event_kind = ("selection_unchanged" if base == trial else
                          "offer_adopted" if choice["candidate_id"] == trial else "offer_not_adopted")
            self.event(event_kind, offer_ref=selected["ref"], decision=choice)

    def finalize(self):
        focus_id = (self.active_focus() or {}).get("id")
        super().finalize()
        # Existing closure handles the same four calls. No new query can be opened here.
        self.apply_disposition(self._final_choice, focus_id)

    def event(self, kind, **value):
        if kind == "final_selection":
            self._final_choice = copy.deepcopy(value["decision"])
        super().event(kind, **value)

    def run(self):
        result = super().run()
        for focus in self.focus_history:
            if focus["status"] == "pending":
                focus["status"] = "deferred"
                self.event("focus_deferred", focus_id=focus["id"], reason=self.stop_reason)
        result.update(protocol=PROTOCOL, system="coreta_workboard_d0",
                      focus_history=copy.deepcopy(self.focus_history))
        write_json(self.journal.root / "result.json", result)
        return result
