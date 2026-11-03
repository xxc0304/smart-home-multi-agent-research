"""V2 baselines retain frozen scheduling, with task-sized ranking rendering."""
import copy
from ..handoff.runtime import Runner
from .ranking import render_ranking


class RankingRunner(Runner):
    selected_member = None
    def full_answer(self, agent):
        if self.selected_member is not None and agent != self.selected_member:
            return None
        value = self.gateway.call("INDEPENDENT", agent, self.packet(agent, "INDEPENDENT"))
        artifact = render_ranking(value["ranking"])
        self.independent[agent] = artifact
        self.independent_details[agent] = copy.deepcopy(value)
        self.event("independent_answer", member=agent, artifact=artifact, structured=value)
        return artifact

    def ordinary(self):
        # Collect all independent answers BEFORE publishing them into any discussion packet.
        for agent in self.agents:
            self.full_answer(agent)
        for agent in self.agents:
            self.discussion.append({"author": agent, "kind": "initial",
                                    **copy.deepcopy(self.independent_details[agent])})
        self.work = {"ref": "W1", "artifact": self.independent[self.driver], "unresolved": [],
                     "ranking": list(self.independent_details[self.driver]["ranking"]),
                     "explanation": self.independent_details[self.driver]["explanation"],
                     "application_history": [], "changed_text": True,
                     "origin": "driver_initial_fallback_not_selected_by_score"}
        self.works.append(copy.deepcopy(self.work))
        self.event("ordinary_initial_fallback", work_ref=self.work["ref"])
        for round_number in range(2):
            for agent in self.agents:
                value = self.gateway.call("DISCUSS", agent, self.packet(agent, "DISCUSS"))
                self.discussion.append({"author": agent, "kind": "discussion", "round": round_number + 1, "text": value["text"]})
                self.event("discussion", member=agent, round=round_number + 1, text=value["text"])
        value = self.gateway.call("FINAL", self.driver, self.packet(self.driver, "FINAL"))
        artifact = render_ranking(value["ranking"])
        self.work = {"ref": f"W{len(self.works) + 1}", "artifact": artifact, "unresolved": [],
                     "ranking": list(value["ranking"]), "explanation": value["explanation"],
                     "application_history": [], "changed_text": artifact != self.work["artifact"]}
        self.works.append(copy.deepcopy(self.work))
        self.event("ordinary_final", artifact=artifact, structured=value)
        return "discussion_finished"
