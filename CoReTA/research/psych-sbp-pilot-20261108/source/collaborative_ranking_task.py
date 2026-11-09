"""Base class for collaborative ranking tasks.

This class contains all the generic logic for collaborative ranking tasks,
including expert information distribution, decision modes, adversarial agents,
and collaboration facilitation. Task-specific content (items, specialized info,
ground truth) is provided by derived classes.
"""

import os
import random
import re
from abc import abstractmethod
from collections import defaultdict
from typing import Dict, List, Tuple

from teamwork.agent import TeamAgent
from teamwork.backends import AnthropicBackend
from teamwork.conversation import Turn
from teamwork.tasks.task import Task, TaskResult


class CollaborativeRankingTask(Task):
    """Base class for collaborative ranking tasks.

    Derived classes must implement:
    - items property: List of items to rank
    - specialized_information property: List of specialized info per item
    - ground_truth_ranking property: Ground truth ranking (1-indexed)
    - get_task_description: Task-specific scenario description
    - get_adversarial_prompt: Task-specific adversarial prompt
    - _parse_ranking: Task-specific ranking parsing
    """

    def __init__(
        self,
        agent_ids: List[int],
        max_rounds: int,
        expert_info_mode: str = "none",
        seed: int | None = None,
        interactive_brainstorming_mode: bool = False,
        decision_mode: str = "expert_not_mentioned",
        num_adversarial_agents: int = 0,
        adversarial_mode: str = "none",
        randomize_speaking_order: bool = True,
        randomize_final_submitter: bool = True,
        name: str | None = None,
    ):
        """Initialize collaborative ranking task.

        Args:
            agent_ids: List of unique agent IDs that will work on this task
            max_rounds: Maximum number of collaboration rounds (required)
            expert_info_mode: Expert information distribution mode ("none", "full", "single_expert", "distributed")
            seed: Random seed for shuffling item presentation order (required)
            interactive_brainstorming_mode: Whether to use interactive brainstorming (True) or nominal brainstorming with individual rankings (False).
            decision_mode: Decision strategy for team collaboration ("expert_not_mentioned", "discussion_based_expert_identification", "explicit_expert_voting", "worse_than_expert_voting", "reveal_expert", "reveal_distributed_experts").
            num_adversarial_agents: Number of adversarial agents (0 = disabled)
            adversarial_mode: Adversarial mode ("none", "with_ground_truth", "without_ground_truth")
            randomize_speaking_order: If True (default), randomize the speaking order in each round. If False, agents speak in fixed order (agent_ids order).
            randomize_final_submitter: If True (default), randomly select a non-adversarial agent to submit the final ranking. If False, always use agent 0 (or first non-adversarial agent).
            name: Optional human-readable name for the task
        """
        super().__init__(agent_ids, max_rounds, name)
        self.expert_info_mode = expert_info_mode
        self.interactive_brainstorming_mode = interactive_brainstorming_mode
        self.decision_mode = decision_mode
        self.num_adversarial_agents = num_adversarial_agents
        self.adversarial_mode = adversarial_mode
        self.randomize_speaking_order = randomize_speaking_order
        self.randomize_final_submitter = randomize_final_submitter
        self.seed = seed
        self.revealed_expert_agent_id = None  # Tracks expert for reveal_expert mode
        self.designated_expert_agent_id = None  # Tracks expert for single_expert mode
        self.adversarial_agent_ids: List[int] = []  # Tracks adversarial agents
        self.coordinator_agent_id: int | None = None  # Tracks coordinator for voting-based decision modes
        self.explicit_voting_votes: Dict[int, int | None] = {}  # Maps agent_id to their voted agent_id
        self.declared_best_agent_id: int | None = None  # Agent declared by coordinator as having the best ranking
        self.worse_than_assessments: Dict[int, List[Tuple[int, str]]] = {}  # Maps assessor_agent_id -> [(worse_agent_id, explanation), ...]
        self.worse_than_counts: Dict[int, int] = {}  # Maps agent_id -> count of "worse than" mentions
        self.information_assigned_per_expert: Dict[int, List[str]] = defaultdict(list)  # Maps agent_id to list of specialized info pieces assigned
        self.items_expert_in_per_agent: Dict[int, List[str]] = defaultdict(list)  # Maps agent_id to list of items they are expert in (for distributed mode)

        # Validate expert_info_mode
        valid_expert_info_modes = ["none", "full", "single_expert", "distributed"]
        if self.expert_info_mode not in valid_expert_info_modes:
            raise ValueError(f"expert_info_mode must be one of {valid_expert_info_modes}, got '{self.expert_info_mode}'")

        valid_decision_modes = ["expert_not_mentioned", "discussion_based_expert_identification", "explicit_expert_voting", "worse_than_expert_voting", "reveal_expert", "reveal_distributed_experts"]
        if self.decision_mode not in valid_decision_modes:
            raise ValueError(f"decision_mode must be one of {valid_decision_modes}, got '{self.decision_mode}'")
        
        # Validate decision_mode and expert_info_mode compatibility
        if self.decision_mode == "reveal_expert" and self.expert_info_mode != "single_expert":
            raise ValueError(f"decision_mode 'reveal_expert' can only be used with expert_info_mode='single_expert', got expert_info_mode='{self.expert_info_mode}'")
        
        if self.decision_mode == "reveal_distributed_experts" and self.expert_info_mode != "distributed":
            raise ValueError(f"decision_mode 'reveal_distributed_experts' can only be used with expert_info_mode='distributed', got expert_info_mode='{self.expert_info_mode}'")

        # Voting-based modes require nominal brainstorming mode (individual rankings must be stated)
        if self.decision_mode in ["explicit_expert_voting", "worse_than_expert_voting"] and self.interactive_brainstorming_mode:
            raise ValueError(
                f"decision_mode '{self.decision_mode}' requires interactive_brainstorming_mode=False. "
                f"Voting-based expert identification requires individual rankings to be stated before voting/assessment."
            )

        # Validate adversarial mode
        valid_adversarial_modes = ["none", "with_ground_truth", "without_ground_truth"]
        if self.adversarial_mode not in valid_adversarial_modes:
            raise ValueError(f"adversarial_mode must be one of {valid_adversarial_modes}, got '{self.adversarial_mode}'")

        if self.adversarial_mode != "none" and self.num_adversarial_agents == 0:
            raise ValueError("num_adversarial_agents must be > 0 when adversarial_mode != 'none'")

        if self.num_adversarial_agents > 0:
            if self.adversarial_mode == "none":
                raise ValueError("adversarial_mode must not be 'none' when num_adversarial_agents > 0")

            # Ensure at least 1 non-adversarial agent remains (needed for final ranking submission)
            if self.num_adversarial_agents >= len(agent_ids):
                raise ValueError(f"num_adversarial_agents ({self.num_adversarial_agents}) must be < total_agents ({len(agent_ids)}) to ensure at least 1 non-adversarial agent remains")

            # Check if expert info mode requires expert selection
            if self.expert_info_mode == "single_expert" and self.num_adversarial_agents >= len(agent_ids):
                raise ValueError(f"num_adversarial_agents ({self.num_adversarial_agents}) must be < total_agents ({len(agent_ids)}) when expert_info_mode is 'single_expert'")

        # Shuffle items once for all agents using the provided seed
        rng = random.Random(seed)
        self.shuffled_items = self.items.copy()
        rng.shuffle(self.shuffled_items)

    # Abstract properties - must be implemented by derived classes
    @property
    @abstractmethod
    def items(self) -> List[str]:
        """List of items to rank."""
        ...

    @property
    @abstractmethod
    def specialized_information(self) -> List[str]:
        """List of specialized information pieces, one per item."""
        ...

    @property
    @abstractmethod
    def ground_truth_ranking(self) -> List[int]:
        """Ground truth ranking (0-indexed, where 0 = most important, N-1 = least important)."""
        ...

    # Abstract methods - must be implemented by derived classes
    @abstractmethod
    def get_task_description(self, agent_id: int) -> str:
        """Return the task description for a specific agent.

        Args:
            agent_id: The ID of the agent requesting the task description

        Returns:
            Task description string tailored for this agent
        """
        ...

    @abstractmethod
    def get_adversarial_prompt(self, agent_id: int) -> str:
        """Return adversarial prompt for an adversarial agent.

        Args:
            agent_id: ID of the adversarial agent

        Returns:
            Complete adversarial prompt with scenario context and adversarial instructions
        """
        ...

    @abstractmethod
    def _parse_ranking(self, text: str) -> Dict[str, int]:
        """Parse a ranking from text and return as dict of item name to rank.

        Args:
            text: Text containing a numbered ranking of items

        Returns:
            Dictionary mapping item name to assigned rank (1-indexed)

        Raises:
            ValueError: If ranking is incomplete or invalid
        """
        ...

    def get_hidden_info(self, agent_id: int) -> str:
        """Return agent-specific perspective for the task (for backward compatibility).

        This method is kept for compatibility with the abstract base class.
        It returns the information assigned to the agent based on expert_info_mode.
        
        Args:
            agent_id: ID of the agent requesting hidden information
            
        Returns:
            Hidden information string for this agent (empty if none assigned)
        """
        self.validate_agent_id(agent_id)
        
        # Return the information assigned to this agent
        assigned_info = self.information_assigned_per_expert.get(agent_id, [])
        return "\n\n".join(assigned_info)

    def score_solution(self, solution: str) -> float:
        """Score a ranking solution using L1 distance from ground truth ranking.

        Args:
            solution: String containing the final team ranking

        Returns:
            L1 distance from ground truth ranking (lower is better)
        """
        try:
            ranking_dict = self._parse_ranking(solution)
            l1_distance = 0.0
            for i, item in enumerate(self.items):
                model_rank = ranking_dict[item]
                expert_rank = self.ground_truth_ranking[i]
                l1_distance += abs(model_rank - expert_rank)
            return float(l1_distance)

        except Exception as e:
            print(f"Error parsing ranking: {e}")
            # Return worst possible score (complete reversal of ranking)
            # For n items, worst case L1 distance is sum(|n - 2i - 1|) for i=0 to n-1
            # For odd n: (n-1)*(n+1)/2, for even n: n*n/2
            num_items = len(self.items)
            if num_items % 2 == 0:
                worst_score = num_items * num_items / 2
            else:
                worst_score = (num_items - 1) * (num_items + 1) / 2
            return float(worst_score)

    def _select_adversarial_agents(self, excluded_agent_ids: List[int] | None = None) -> None:
        """Select adversarial agents from available pool, excluding specified agents.

        Args:
            excluded_agent_ids: List of agent IDs to exclude from selection (e.g., expert agent)
        """
        if excluded_agent_ids is None:
            excluded_agent_ids = []

        available_agents = [aid for aid in self.agent_ids if aid not in excluded_agent_ids]
        
        if len(available_agents) < self.num_adversarial_agents:
            raise ValueError(
                f"Cannot select {self.num_adversarial_agents} adversarial agents from "
                f"{len(available_agents)} available agents (excluding {excluded_agent_ids})"
            )

        rng = random.Random(self.seed)
        selected = rng.sample(available_agents, self.num_adversarial_agents)
        self.adversarial_agent_ids = sorted(selected)

    def get_full_info(self) -> str:
        """Return complete ground truth analysis for all items.

        Returns all specialized information items for use in full expert_info_mode.
        """
        return "\n\n".join(self.specialized_information)

    def _assign_expert_information(self, agents: List[TeamAgent]) -> None:
        """Assign expert information to all agents based on expert_info_mode.
        
        Populates self.information_assigned_per_expert dictionary mapping agent_id to list of info strings.
        Adversarial agents are always excluded from receiving expert information (they will have empty lists).
        
        Args:
            agents: List of all agents participating in the task
        """
        # Get list of non-adversarial agents (computed once for efficiency)
        non_adversarial_agents = [a for a in agents if a.profile.agent_id not in self.adversarial_agent_ids]
        
        if self.expert_info_mode == "none":
            # No agents receive expert information (adversarial agents already have empty lists via defaultdict)
            return
        
        elif self.expert_info_mode == "full":
            # All non-adversarial agents receive all pieces
            for agent in non_adversarial_agents:
                self.information_assigned_per_expert[agent.profile.agent_id] = self.specialized_information.copy()
        
        elif self.expert_info_mode == "single_expert":
            # One randomly selected non-adversarial agent receives all pieces
            if not non_adversarial_agents:
                raise ValueError("Cannot assign expert information: no non-adversarial agents available")
            
            # Select expert if not already selected
            if self.designated_expert_agent_id is None:
                rng = random.Random(self.seed)
                expert_agent = rng.choice(non_adversarial_agents)
                self.designated_expert_agent_id = expert_agent.profile.agent_id
                
                # Select adversarial agents after expert is selected (exclude expert)
                if self.num_adversarial_agents > 0:
                    self._select_adversarial_agents(excluded_agent_ids=[self.designated_expert_agent_id])
                    # Recompute non-adversarial agents after adversarial selection
                    non_adversarial_agents = [a for a in agents if a.profile.agent_id not in self.adversarial_agent_ids]
            
            # Assign all info to designated expert
            self.information_assigned_per_expert[self.designated_expert_agent_id] = self.specialized_information.copy()
        
        elif self.expert_info_mode == "distributed":
            # Distribute all pieces in round-robin fashion among non-adversarial agents
            if not non_adversarial_agents:
                raise ValueError("Cannot assign expert information: no non-adversarial agents available")
            
            num_hidden_information_items = len(self.specialized_information)
            num_non_adversarial = len(non_adversarial_agents)
            
            if num_non_adversarial > num_hidden_information_items:
                raise ValueError(f"Cannot have more than {num_hidden_information_items} non-adversarial agents (got {num_non_adversarial}) for distributed mode. Each agent needs at least one unique info piece.")
            
            # Distribute in round-robin fashion
            for i, info_piece in enumerate(self.specialized_information):
                agent_index = i % num_non_adversarial
                agent_id = non_adversarial_agents[agent_index].profile.agent_id
                self.information_assigned_per_expert[agent_id].append(info_piece)
                # Also track which item this agent is expert in (specialized_information[i] corresponds to items[i])
                self.items_expert_in_per_agent[agent_id].append(self.items[i])

    def _calculate_efficiency_metrics(self, agents: List) -> Dict:
        """Calculate efficiency metrics including token usage and word counts.

        Args:
            agents: List of TeamAgent instances

        Returns:
            Dictionary containing efficiency metrics
        """
        # Aggregate token usage from all agent backends
        total_input_tokens = 0
        total_output_tokens = 0
        agent_token_stats = {}

        for agent in agents:
            agent_id = agent.profile.agent_id
            backend = agent.backend
            stats = backend.usage_stats

            total_input_tokens += stats.input_tokens
            total_output_tokens += stats.output_tokens

            agent_token_stats[f"agent_{agent_id}_total_input_tokens"] = stats.input_tokens
            agent_token_stats[f"agent_{agent_id}_total_output_tokens"] = stats.output_tokens

        # Calculate conversation metrics from agent trajectories
        # Use first agent's trajectory as it contains full conversation
        if agents:
            trajectory = agents[0].trajectory
            total_turns = len(trajectory.turns)

            # Calculate total words in conversation
            total_words = sum(len(turn.content.split()) for turn in trajectory.turns)

            # Calculate per-agent word counts
            agent_word_counts = {agent_id: 0 for agent_id in self.agent_ids}
            for turn in trajectory.turns:
                if turn.speaker_id in agent_word_counts:
                    agent_word_counts[turn.speaker_id] += len(turn.content.split())

            per_agent_words = {
                f"agent_{agent_id}_word_count": count
                for agent_id, count in agent_word_counts.items()
            }
        else:
            total_turns = 0
            total_words = 0
            per_agent_words = {}

        return {
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_conversation_turns": total_turns,
            "total_conversation_words": total_words,
            **agent_token_stats,
            **per_agent_words
        }

    def execute(self, agents: List[TeamAgent]) -> TaskResult:
        """Execute the collaborative ranking task with independent then collaborative phases.

        Args:
            agents: List of agents to participate in the task

        Returns:
            TaskResult containing the final solution and score
        """
        if len(agents) != len(self.agent_ids):
            raise ValueError(f"Expected {len(self.agent_ids)} agents, got {len(agents)}")

        agent_map = {agent.profile.agent_id: agent for agent in agents}
        for agent_id in self.agent_ids:
            if agent_id not in agent_map:
                raise ValueError(f"Missing agent with ID {agent_id}")

        # Select adversarial agents if needed
        # For single_expert mode, expert is selected first, then adversarial agents (excluding expert)
        # For other modes, select adversarial agents early before expert info distribution
        if self.num_adversarial_agents > 0 and self.expert_info_mode != "single_expert":
            self._select_adversarial_agents(excluded_agent_ids=[])

        # Phase 1: Independent rankings (always collected for baseline metrics)
        individual_rankings = self._collect_individual_rankings(agents)

        # Phase 2: Collaborative ranking
        final_ranking = self._facilitate_collaboration(agents, individual_rankings, self.interactive_brainstorming_mode)

        # Score the final solution
        score = self.score_solution(final_ranking)

        # Calculate individual agent scores and their distances from final ranking
        individual_scores = {}
        individual_distances_from_final = {}

        for agent_id, ranking_text in individual_rankings.items():
            individual_scores[agent_id] = self.score_solution(ranking_text)

            # Calculate L1 distance between individual and final ranking
            try:
                individual_parsed = self._parse_ranking(ranking_text)
                final_parsed = self._parse_ranking(final_ranking)
                distance = sum(abs(individual_parsed[item] - final_parsed[item]) for item in self.items)
                individual_distances_from_final[agent_id] = float(distance)
            except Exception:
                individual_distances_from_final[agent_id] = None

        # Calculate aggregate individual ranking metrics
        average_individual_score = None
        best_individual_score = None
        nominal_ranking = None
        nominal_score = None

        if individual_scores:
            scores_list = list(individual_scores.values())
            average_individual_score = sum(scores_list) / len(scores_list)
            best_individual_score = min(scores_list)

            # Calculate nominal ranking (average rank for each item across all agents)
            nominal_ranking = self._calculate_nominal_ranking(individual_rankings)
            if nominal_ranking:
                nominal_score = self.score_solution(nominal_ranking)

        # Calculate efficiency metrics
        efficiency_metrics = self._calculate_efficiency_metrics(agents)

        # Build metadata dict with decision mode info
        metadata = {
            "individual_rankings": individual_rankings,
            "individual_scores": individual_scores,
            "individual_distances_from_final": individual_distances_from_final,
            "average_individual_score": average_individual_score,
            "best_individual_score": best_individual_score,
            "nominal_ranking": nominal_ranking,
            "nominal_score": nominal_score,
            "agent_count": len(agents),
            "task_type": self.__class__.__name__.lower().replace("task", ""),
            "expert_info_mode": self.expert_info_mode,
            "interactive_brainstorming_mode": self.interactive_brainstorming_mode,
            "decision_mode": self.decision_mode,
            "information_assigned_per_expert": {str(agent_id): info_list for agent_id, info_list in self.information_assigned_per_expert.items()},
            "items_expert_in_per_agent": {str(agent_id): items_list for agent_id, items_list in self.items_expert_in_per_agent.items()},
            **efficiency_metrics
        }

        # Add expert agent ID for reveal_expert mode
        if self.revealed_expert_agent_id is not None:
            metadata["revealed_expert_agent_id"] = self.revealed_expert_agent_id

        # Add expert info for single_expert mode
        if self.designated_expert_agent_id is not None:
            metadata["designated_expert_agent_id"] = self.designated_expert_agent_id

        # Add expert identification info for voting-based modes
        if self.decision_mode in ["explicit_expert_voting", "worse_than_expert_voting"]:
            if self.coordinator_agent_id is not None:
                metadata["coordinator_agent_id"] = self.coordinator_agent_id
            if self.declared_best_agent_id is not None:
                metadata["declared_best_agent_id"] = self.declared_best_agent_id
            if self.explicit_voting_votes:
                metadata["explicit_voting_votes"] = self.explicit_voting_votes
            if self.worse_than_assessments:
                # Convert tuples to lists for JSON serialization
                metadata["worse_than_assessments"] = {
                    str(assessor_id): [[worse_id, explanation] for worse_id, explanation in assessments_list]
                    for assessor_id, assessments_list in self.worse_than_assessments.items()
                }
            if self.worse_than_counts:
                metadata["worse_than_counts"] = {str(agent_id): count for agent_id, count in self.worse_than_counts.items()}

        # Add adversarial agent info
        if self.num_adversarial_agents > 0:
            metadata["adversarial_agent_ids"] = self.adversarial_agent_ids
            metadata["num_adversarial_agents"] = len(self.adversarial_agent_ids)
            metadata["adversarial_mode"] = self.adversarial_mode
        else:
            metadata["adversarial_agent_ids"] = []
            metadata["num_adversarial_agents"] = 0
            metadata["adversarial_mode"] = None
        
        # Add per-round rankings (always collected)
        if hasattr(self, 'per_round_rankings'):
            metadata["per_round_rankings"] = self.per_round_rankings
            
            # Also calculate scores for each per-round ranking
            per_round_scores: Dict[int, Dict[int, float]] = {}
            for round_num, rankings in self.per_round_rankings.items():
                round_scores = {}
                for agent_id, ranking_text in rankings.items():
                    score = self.score_solution(ranking_text)
                    round_scores[agent_id] = score
                    # Debug logging to verify scores are being calculated correctly
                    print(f"Per-round score: Round {round_num}, Agent {agent_id}: {score}")
                per_round_scores[round_num] = round_scores
            metadata["per_round_scores"] = per_round_scores

        return TaskResult(
            solution=final_ranking,
            score=score,
            metadata=metadata
        )

    def _collect_individual_rankings(self, agents: List[TeamAgent]) -> Dict[int, str]:
        """Collect individual rankings from each agent independently.

        Each agent maintains their independent response in their trajectory as memory.

        Args:
            agents: List of agents to collect rankings from
        """
        rankings = {}

        # Assign expert information to all agents based on expert_info_mode
        self._assign_expert_information(agents)

        for agent in agents:
            # Get task description (all agents, including adversarial, get task description)
            task_desc = self.get_task_description(agent.profile.agent_id)

            # Get assigned information for this agent
            # Note: Adversarial agents will have empty lists (excluded in _assign_expert_information)
            assigned_info = self.information_assigned_per_expert[agent.profile.agent_id]

            # Build context based on expert_info_mode
            if self.expert_info_mode == "none":
                # No expert information (adversarial agents also get no expert info)
                context = f"{task_desc}\n\n"
            elif self.expert_info_mode == "full":
                # All non-adversarial agents get all info (they know others have it too)
                if assigned_info:
                    full_info = "\n\n".join(assigned_info)
                    context = f"{task_desc}\n\nNASA Ground Truth Analysis: {full_info}\n\n"
                else:
                    # Adversarial agent - no expert info
                    context = f"{task_desc}\n\n"
            elif self.expert_info_mode == "single_expert":
                # Only designated expert gets info, and they're told they're the only one
                if assigned_info:
                    expert_info = "\n\n".join(assigned_info)
                    context = f"{task_desc}\n\nAdditional context that ONLY YOU KNOW and NO OTHER TEAMMATE KNOWS:\n{expert_info}\n\n"
                else:
                    # Non-expert or adversarial agent - no expert info
                    context = f"{task_desc}\n\n"
            elif self.expert_info_mode == "distributed":
                # Each agent gets their assigned pieces, and they're told they're the only one
                if assigned_info:
                    distributed_info = "\n\n".join(assigned_info)
                    context = f"{task_desc}\n\nAdditional context that ONLY YOU KNOW and NO OTHER TEAMMATE KNOWS:\n{distributed_info}\n\n"
                else:
                    # Adversarial agent - no expert info
                    context = f"{task_desc}\n\n"
            else:
                context = f"{task_desc}\n\n"

            # Add context to trajectory so agent can refer back to it
            context_turn = Turn(speaker_id=-1, content=context)
            agent.trajectory.append(context_turn)

            turn = agent.act()
            rankings[agent.profile.agent_id] = turn.content

        print(f"Done with individual rankings from {len(agents)} agents")
        return rankings


    def _extract_expert_vote(self, text: str) -> int | None:
        """Extract expert vote from agent response using regex.
        
        Looks for pattern: "My vote for the best expert is Agent X because ..."
        or "I identify Agent X as having the strongest baseline ranking"
        
        Args:
            text: Agent's response text
            
        Returns:
            Agent ID of voted expert, or None if not found
        """
        # Pattern to match "My vote for the best expert is Agent X" where X is a number
        # Case insensitive and flexible with whitespace
        pattern = r'my vote for the best expert is agent\s+(\d+)'
        match = re.search(pattern, text.lower())
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        
        # Alternative pattern: "I identify Agent X"
        pattern = r'i identify agent\s+(\d+)'
        match = re.search(pattern, text.lower())
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        
        return None


    def _extract_worse_than_agents(self, text: str, assessor_agent_id: int, agent_ids: List[int]) -> List[Tuple[int, str]]:
        """Extract worse-than assessments from agent response.
        
        Parses structured format: "Agent X\nExplanation: [text]"
        Falls back to Claude 4.5 if regex parsing fails.
        
        Args:
            text: Agent's response text
            assessor_agent_id: ID of the agent providing the assessment
            agent_ids: List of valid agent IDs
            
        Returns:
            List of tuples (worse_agent_id, explanation)
        """
        text_lower = text.lower().strip()
        
        # Check for "No agents are worse than me"
        if "no agents are worse than me" in text_lower:
            return []
        
        # Try regex parsing first
        assessments = []
        lines = text.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            # Look for "Agent X" pattern
            agent_match = re.match(r'^agent\s+(\d+)', line, re.IGNORECASE)
            if agent_match:
                try:
                    agent_id = int(agent_match.group(1))
                    # Validate agent ID
                    if agent_id not in agent_ids or agent_id == assessor_agent_id:
                        i += 1
                        continue
                    
                    # Look for "Explanation:" on next line(s)
                    explanation_parts = []
                    j = i + 1
                    found_explanation = False
                    while j < len(lines):
                        next_line = lines[j].strip()
                        if next_line.lower().startswith('explanation:'):
                            found_explanation = True
                            explanation_text = next_line[len('explanation:'):].strip()
                            if explanation_text:
                                explanation_parts.append(explanation_text)
                            j += 1
                            # Continue collecting explanation text until next "Agent X" or empty line
                            while j < len(lines):
                                next_line = lines[j].strip()
                                if not next_line or re.match(r'^agent\s+\d+', next_line, re.IGNORECASE):
                                    break
                                explanation_parts.append(next_line)
                                j += 1
                            break
                        elif not next_line:
                            break
                        j += 1
                    
                    if found_explanation:
                        explanation = ' '.join(explanation_parts).strip()
                        if explanation:
                            assessments.append((agent_id, explanation))
                        i = j
                    else:
                        i += 1
                except ValueError:
                    i += 1
            else:
                i += 1
        
        # If regex parsing found assessments, return them
        if assessments:
            return assessments
        
        # If no assessments found and not explicitly saying "no agents", try Claude fallback
        if "no agents are worse than me" not in text_lower:
            try:
                return self._extract_worse_than_with_claude(text, assessor_agent_id, agent_ids)
            except Exception as e:
                print(f"Warning: Claude fallback failed for agent {assessor_agent_id}: {e}")
                return []
        
        return []


    def _extract_worse_than_with_claude(self, text: str, assessor_agent_id: int, agent_ids: List[int]) -> List[Tuple[int, str]]:
        """Use Claude 4.5 to extract worse-than assessments when regex parsing fails.
        
        Args:
            text: Agent's response text
            assessor_agent_id: ID of the agent providing the assessment
            agent_ids: List of valid agent IDs
            
        Returns:
            List of tuples (worse_agent_id, explanation)
        """
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_api_key:
            print("Warning: ANTHROPIC_API_KEY not found, cannot use Claude fallback")
            return []
        
        backend = AnthropicBackend(api_key=anthropic_api_key, model="claude-3-5-sonnet-20241022")
        
        valid_agent_ids_str = ", ".join(str(aid) for aid in agent_ids if aid != assessor_agent_id)
        prompt = f"""Extract the worse-than assessments from the following agent response.

The agent (Agent {assessor_agent_id}) was asked to identify which agents have worse rankings or reasoning than them.

Valid agent IDs (excluding Agent {assessor_agent_id}): {valid_agent_ids_str}

Agent response:
{text}

Extract all agents that were identified as worse than Agent {assessor_agent_id}, along with their explanations.

Return the result as a JSON list of objects, each with "agent_id" (integer) and "explanation" (string).
If no agents were identified as worse, return an empty list.
If the agent said "No agents are worse than me" or similar, return an empty list.

Example format:
[
  {{"agent_id": 2, "explanation": "Agent 2's ranking prioritizes less critical items"}},
  {{"agent_id": 5, "explanation": "Agent 5's reasoning lacks consideration of oxygen needs"}}
]

Return ONLY the JSON array, no other text."""
        
        try:
            from teamwork.profiles import AgentProfile
            from teamwork.conversation import Trajectory
            
            profile = AgentProfile(agent_id=-1, name="Parser", role="Parser", system_prompt="")
            trajectory = Trajectory()
            trajectory.append(Turn(speaker_id=-1, content=prompt))
            
            response_text = backend.invoke(agent_profile=profile, trajectory=trajectory)
            
            # Parse JSON response
            import json
            # Try to extract JSON array from response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)
                parsed = json.loads(json_text)
                assessments = []
                for item in parsed:
                    if isinstance(item, dict) and "agent_id" in item and "explanation" in item:
                        agent_id = int(item["agent_id"])
                        if agent_id in agent_ids and agent_id != assessor_agent_id:
                            assessments.append((agent_id, str(item["explanation"])))
                return assessments
        except Exception as e:
            print(f"Warning: Failed to parse Claude response: {e}")
        
        return []


    def _collect_expert_votes(self, agents: List[TeamAgent], individual_rankings: Dict[int, str]) -> Dict[int, int | None]:
        """Collect independent expert votes from each agent.
        
        Each agent independently decides who they think is the expert based on
        the rankings they've seen. Their votes are collected before sharing.
        
        Args:
            agents: List of agents to collect votes from
            individual_rankings: Dict mapping agent_id to their ranking text
            
        Returns:
            Dict mapping voter_agent_id to voted_expert_id
        """
        votes = {}
        other_agent_ids = self.agent_ids.copy()
        
        for agent in agents:
            agent_id = agent.profile.agent_id
            other_agents_list = [aid for aid in other_agent_ids if aid != agent_id]
            other_agents_str = ", ".join(f"Agent {aid}" for aid in other_agents_list)
            
            # Build prompt asking agent to vote on expert
            vote_prompt = f"""You are Agent {agent_id}. You are working with {len(self.agent_ids) - 1} other agents ({other_agents_str}).

You have now seen everyone's individual rankings. Based on the quality of reasoning, survival priorities, and overall soundness of each ranking, you need to independently decide which agent has the best ranking.

IMPORTANT: Do NOT prioritize your own ranking. Assess all rankings, including your own, objectively based on their merit.

Please provide your vote in this EXACT format:
"My vote for the best expert is Agent [X] because [your reasoning explaining why this agent's ranking demonstrates the clearest survival priorities and most sound reasoning]."

Where [X] is the agent ID (0-{len(self.agent_ids) - 1}) of the agent you believe has the strongest ranking, and [your reasoning] as to why.

After you state your vote, you will hear the reasoning and vote of the other members of the team."""
            
            # Add prompt to agent's trajectory as system message
            prompt_turn = Turn(speaker_id=-1, content=vote_prompt)
            agent.trajectory.append(prompt_turn)
            
            # Get agent's response
            turn = agent.act()
            vote_text = turn.content
            
            # Extract the vote using regex
            voted_expert_id = self._extract_expert_vote(vote_text)
            
            if voted_expert_id is not None:
                # Validate the voted expert ID is valid
                if voted_expert_id in self.agent_ids:
                    votes[agent_id] = voted_expert_id
                else:
                    print(f"Warning: Agent {agent_id} voted for invalid agent ID {voted_expert_id}. Storing None.")
                    votes[agent_id] = None
            else:
                print(f"Warning: Could not extract expert vote from Agent {agent_id}'s response: {vote_text[:100]}. Storing None.")
                votes[agent_id] = None
        
        return votes


    def _collect_worse_than_assessments(self, agents: List[TeamAgent], individual_rankings: Dict[int, str]) -> Dict[int, List[Tuple[int, str]]]:
        """Collect worse-than assessments from each agent.
        
        Each agent independently identifies which agents they think have worse rankings
        or reasoning than themselves, along with explanations.
        
        Args:
            agents: List of agents to collect assessments from
            individual_rankings: Dict mapping agent_id to their ranking text
            
        Returns:
            Dict mapping assessor_agent_id -> [(worse_agent_id, explanation), ...]
        """
        assessments = {}
        other_agent_ids = self.agent_ids.copy()
        
        for agent in agents:
            agent_id = agent.profile.agent_id
            other_agents_list = [aid for aid in other_agent_ids if aid != agent_id]
            other_agents_str = ", ".join(f"Agent {aid}" for aid in other_agents_list)
            
            # Build prompt asking agent to identify worse agents
            worse_than_prompt = f"""You are Agent {agent_id}. You are working with {len(self.agent_ids) - 1} other agents ({other_agents_str}).

You have now seen everyone's individual rankings. Based on the quality of reasoning, survival priorities, and overall soundness of each ranking, identify which agents you think have worse rankings or reasoning than you.

You MUST use this exact format for each agent you identify:

Agent [X]
Explanation: [your explanation]

For example, if you are Agent {agent_id} and think Agents 5 and 7 are worse than you:

Agent 5
Explanation: [explanation for why Agent 5 is worse]

Agent 7
Explanation: [explanation for why Agent 7 is worse]

You can identify zero, one, or multiple agents. If you think no one is worse than you, 
you must say exactly: "No agents are worse than me". It is possible that no one is worse than you, so do not assume that everyone is worse than you.

IMPORTANT: You MUST comply with this format requirement. Each agent you identify should 
be on its own line starting with 'Agent [ID]' followed by 'Explanation:' on the next line."""
            
            # Add prompt to agent's trajectory as system message
            prompt_turn = Turn(speaker_id=-1, content=worse_than_prompt)
            agent.trajectory.append(prompt_turn)
            
            # Get agent's response
            turn = agent.act()
            response_text = turn.content
            
            # Extract the worse-than assessments
            worse_than_list = self._extract_worse_than_agents(response_text, agent_id, self.agent_ids)
            assessments[agent_id] = worse_than_list
            
            if not worse_than_list:
                print(f"Agent {agent_id} identified no agents as worse than them")
            else:
                print(f"Agent {agent_id} identified {len(worse_than_list)} agent(s) as worse: {[aid for aid, _ in worse_than_list]}")
        
        return assessments


    def _collect_per_round_rankings(self, agents: List[TeamAgent], round_num: int, individual_rankings: Dict[int, str]) -> Dict[int, str]:
        """Collect each agent's current ranking after a round of discussion.
        
        Queries each agent with their initial ranking and the team dialogue so far,
        asking them to provide their current belief about the best ranking.
        
        Args:
            agents: List of agents to collect rankings from
            round_num: Current round number (1-indexed)
            individual_rankings: Dict mapping agent_id to their initial individual ranking
            
        Returns:
            Dict mapping agent_id to their current ranking text
        """
        rankings = {}
        items_list = "\n".join(f"{i+1}. {item}" for i, item in enumerate(self.shuffled_items))
        
        for agent in agents:
            agent_id = agent.profile.agent_id
            other_agent_ids = [aid for aid in self.agent_ids if aid != agent_id]
            other_agents_str = ", ".join(f"Agent {aid}" for aid in other_agent_ids)
            
            # Get the agent's initial ranking
            initial_ranking_full = individual_rankings.get(agent_id, "")
            
            # Extract just the ranking part (skip task description if present)
            # Look for "MY RANKING:" or similar markers, or just take the ranking lines
            initial_ranking = initial_ranking_full
            if "MY RANKING:" in initial_ranking_full:
                # Extract everything after "MY RANKING:"
                initial_ranking = initial_ranking_full.split("MY RANKING:")[-1].strip()
            elif "RANKING:" in initial_ranking_full:
                # Fallback: extract after "RANKING:"
                initial_ranking = initial_ranking_full.split("RANKING:")[-1].strip()
            else:
                # If no marker found, try to extract just numbered lines (the ranking)
                lines = initial_ranking_full.split('\n')
                ranking_lines = []
                for line in lines:
                    # Look for lines that start with a number followed by a period or parenthesis
                    if re.match(r'^\s*\d+[\.\)]\s+', line):
                        ranking_lines.append(line)
                if ranking_lines:
                    initial_ranking = '\n'.join(ranking_lines)
            
            # Build prompt that references initial ranking and conversation so far
            prompt = f"""You are Agent {agent_id}. You are working with {len(self.agent_ids) - 1} other agents ({other_agents_str}).

You have been participating in a team discussion about ranking items. You have completed Round {round_num} of {self.max_rounds} rounds of discussion.

Your initial individual ranking was:
{initial_ranking}

Given your initial ranking and the team dialogue until now, what is your current belief about the best ranking? Please provide:

1. An explanation (at least 3 sentences) of how your thinking has evolved based on the team discussion
2. Your current ranking of ALL {len(self.items)} items in this exact format:

MY CURRENT RANKING:
1. [Item name]
2. [Item name]
...
{len(self.items)}. [Item name]

For reference, here are the EXACT item names to use (copy these exactly):
{items_list}

where [Item name] is the EXACT name of the item in the list above."""
            
            # Add prompt to agent's trajectory as system message
            prompt_turn = Turn(speaker_id=-1, content=prompt)
            agent.trajectory.append(prompt_turn)
            
            # Get agent's response
            turn = agent.act()
            ranking_text = turn.content
            
            # Try to parse the ranking - allow up to 3 attempts total (initial + 2 retries)
            max_retries = 2
            
            for attempt in range(max_retries + 1):
                try:
                    self._parse_ranking(ranking_text)
                    break
                except ValueError as e:
                    if attempt < max_retries:
                        # Retry with more explicit instructions
                        retry_prompt = f"""You are Agent {agent_id}. You are working with {len(self.agent_ids) - 1} other agents ({other_agents_str}).

The ranking you provided could not be parsed. Error: {str(e)}

Please provide your CURRENT RANKING again, ensuring:
- You include ALL {len(self.items)} items (no more, no less)
- Each item appears exactly once
- You use the exact format with numbered lines
- Copy the EXACT item names from the list below

For reference, here are the EXACT item names to use (copy these exactly):
{items_list}

MY CURRENT RANKING:
1. [Item name]
2. [Item name]
...
{len(self.items)}. [Item name]"""
                        
                        # Add retry prompt to trajectory as system message
                        retry_prompt_turn = Turn(speaker_id=-1, content=retry_prompt)
                        agent.trajectory.append(retry_prompt_turn)
                        
                        turn = agent.act()
                        ranking_text = turn.content
                    else:
                        # All retries exhausted - log warning but still store the ranking
                        print(f"Warning: Could not parse ranking for agent {agent_id} after {max_retries + 1} attempts. Storing incomplete ranking.")
                        print(f"Error: {str(e)}")
                        break
            
            rankings[agent_id] = ranking_text
            # Debug logging to verify rankings are being stored correctly
            try:
                parsed = self._parse_ranking(ranking_text)
                score = self.score_solution(ranking_text)
                print(f"Per-round collection: Round {round_num}, Agent {agent_id}: Score={score}, Ranking length={len(parsed)} items")
            except Exception as e:
                print(f"Warning: Could not parse/score ranking for Agent {agent_id} in round {round_num}: {e}")
        
        print(f"Done with per-round rankings from {len(agents)} agents after round {round_num}")
        return rankings


    def _facilitate_collaboration(self, agents: List[TeamAgent], individual_rankings: Dict[int, str], interactive_brainstorming_mode: bool = False) -> str:
        """Facilitate collaborative discussion to reach final team ranking.

        Each agent acts on their own trajectory, but all agents see each other's turns
        by sharing them after each agent speaks.
        """
        # Nominal mode: All agents state their individual rankings
        if not interactive_brainstorming_mode:
            # Randomize the order in which agents state their rankings (if enabled)
            agent_ids_to_state = list(individual_rankings.keys())
            if self.randomize_speaking_order:
                if self.seed is not None:
                    rng = random.Random(self.seed)
                    rng.shuffle(agent_ids_to_state)
                else:
                    random.shuffle(agent_ids_to_state)
            
            for agent_id in agent_ids_to_state:
                ranking = individual_rankings[agent_id]
                turn = Turn(
                    speaker_id=agent_id,
                    content=f"My individual ranking:\n{ranking}"
                )
                # Add stating turn to all agents' trajectories
                for agent in agents:
                    agent.trajectory.append(turn)

        # Add decision mode guidance/revelation (applies to both interactive and nominal modes)
        if self.decision_mode == "reveal_expert":
            # Calculate individual scores to identify best performer (exclude adversarial agents)
            individual_scores: Dict[int, float] = {}
            for agent_id, ranking_text in individual_rankings.items():
                if agent_id not in self.adversarial_agent_ids:
                    individual_scores[agent_id] = self.score_solution(ranking_text)

            # Find agent with lowest score (best performance)
            if not individual_scores:
                raise ValueError("Cannot identify expert: no non-adversarial agents available")
            best_agent_id = min(individual_scores.keys(), key=lambda x: individual_scores[x])
            self.revealed_expert_agent_id = best_agent_id

            yetton_v3_message = f"""Agent {best_agent_id} has been identified as having the most accurate individual ranking based on their performance.

STEP 1 - ADOPTION: Adopt Agent {best_agent_id}'s COMPLETE ranking as your baseline. This ensures you preserve the strongest foundation.

STEP 2 - REFINEMENT: Propose modifications to this baseline ONLY if you can:
  • Point to a specific item placement that may be incorrect
  • Provide clear reasoning or evidence for why a change would improve survival odds
  • Explain how your suggestion builds on or corrects the baseline ranking

Do NOT prioritize your own reasoning over the expert's. The goal is to preserve the expert foundation while incorporating any genuinely valuable insights. Avoid compromising or averaging—either keep the baseline item position, or make a clearly justified change."""

            yetton_v3_turn = Turn(speaker_id=-1, content=yetton_v3_message)
            for agent in agents:
                agent.trajectory.append(yetton_v3_turn)

        elif self.decision_mode == "reveal_distributed_experts":
            # Reveal which items/candidates each agent has privileged information on (without revealing the specialized information)
            expert_revelations = []
            for agent_id in sorted(self.items_expert_in_per_agent.keys()):
                if agent_id not in self.adversarial_agent_ids and self.items_expert_in_per_agent[agent_id]:
                    items = self.items_expert_in_per_agent[agent_id]
                    items_str = ", ".join(items)
                    expert_revelations.append(f"Agent {agent_id} has privileged expert information on the following: {items_str}")
            
            if expert_revelations:
                revelation_message = """The following agents have privileged expert information on specific items:

""" + "\n".join(expert_revelations) + """

STEP 1 - IDENTIFY INFORMATION: Use the information above to understand which agents have specialized knowledge about which items.

STEP 2 - COLLABORATION: When discussing rankings, prioritize the input from agents who have privileged information on those specific items. For example, when ranking items related to navigation, give more weight to the agent who has privileged information on navigation-related items.

STEP 3 - SYNTHESIS: Work together to create a final ranking that incorporates the specialized knowledge from all agents while maintaining a cohesive overall strategy."""
                
                revelation_turn = Turn(speaker_id=-1, content=revelation_message)
                for agent in agents:
                    agent.trajectory.append(revelation_turn)

        elif self.decision_mode == "discussion_based_expert_identification":
            # Discussion-based expert identification: MESLEC research prompt + pure discussion
            meslec_message = """Research shows that groups often perform best when they identify which member's judgment and reasoning are most accurate and build the group decision around that person's ideas, refining them through discussion.
During your deliberation, try to determine who among you seems most competent based on the quality of their arguments, evidence, and reasoning.
Once you believe you have identified that member, start with their proposed ranking and try to improve it, if necessary, with any additional facts or insights offered by others."""

            meslec_turn = Turn(speaker_id=-1, content=meslec_message)
            for agent in agents:
                agent.trajectory.append(meslec_turn)

        elif self.decision_mode == "explicit_expert_voting":
            # Explicit expert voting: MESLEC research prompt + explicit voting with coordinator
            if not interactive_brainstorming_mode:
                # Select a random coordinator agent (exclude adversarial agents)
                available_coordinators = [a for a in agents if a.profile.agent_id not in self.adversarial_agent_ids]
                if not available_coordinators:
                    raise ValueError("No non-adversarial agents available to coordinate expert identification")
                
                if self.seed is not None:
                    rng = random.Random(self.seed)
                    coordinator_agent = rng.choice(available_coordinators)
                else:
                    coordinator_agent = random.choice(available_coordinators)
                
                coordinator_agent_id = coordinator_agent.profile.agent_id
                self.coordinator_agent_id = coordinator_agent_id
                
                meslec_message = f"""Research shows that groups perform best when they identify which member has the most accurate ranking, adopt their solution as a baseline, and then carefully refine it through collaborative reasoning.

STEP 1 - INDEPENDENT VOTING: After everyone has shared their individual rankings, each agent will independently vote on which agent they believe has the strongest ranking. Do NOT prioritize your own ranking—assess all rankings objectively based on their merit. You will be asked to vote and explain your reasoning.

STEP 2 - EXPERT DECLARATION: After all agents have independently voted, a randomly selected team member (Agent {coordinator_agent_id}) will review all the votes and reasoning to declare which agent is identified as having the strongest baseline ranking.

STEP 3 - ADOPTION: Once Agent {coordinator_agent_id} declares the identified expert, the team will adopt that member's COMPLETE ranking as your working baseline. This ensures you preserve the strongest foundation.

STEP 4 - REFINEMENT: Now examine this baseline critically. Other members should propose specific modifications ONLY if they can:
  • Point to a specific item placement that may be incorrect
  • Provide clear reasoning or evidence for why a change would improve survival odds
  • Explain how their suggestion builds on or corrects the baseline ranking

The goal is to preserve the expert foundation while incorporating any genuinely valuable insights from the full team. Avoid compromising or averaging—either keep the baseline item position, or make a clearly justified change."""

                meslec_turn = Turn(speaker_id=-1, content=meslec_message)
                for agent in agents:
                    agent.trajectory.append(meslec_turn)
                
                # Collect independent expert votes from each agent
                expert_votes = self._collect_expert_votes(agents, individual_rankings)
                self.explicit_voting_votes = expert_votes
                
                # Share all votes with all agents (randomize order for stating)
                # Only share votes where we successfully extracted an expert ID (not None)
                agent_ids_to_state_votes = [voter_id for voter_id, voted_id in expert_votes.items() if voted_id is not None]
                if self.randomize_speaking_order:
                    if self.seed is not None:
                        rng = random.Random(self.seed + 1000)  # Use different seed offset for vote stating
                        rng.shuffle(agent_ids_to_state_votes)
                    else:
                        random.shuffle(agent_ids_to_state_votes)
                
                for voter_id in agent_ids_to_state_votes:
                    voted_expert_id = expert_votes[voter_id]
                    # Get the agent's vote response from their trajectory
                    agent = next((a for a in agents if a.profile.agent_id == voter_id), None)
                    if agent is None:
                        continue
                    
                    # Find the last turn from this agent (their vote response)
                    vote_turn = None
                    for turn in reversed(agent.trajectory.turns):
                        if turn.speaker_id == voter_id:
                            vote_turn = turn
                            break
                    
                    if vote_turn:
                        # Share this vote with all other agents (not the voter themselves, since it's already in their trajectory)
                        for other_agent in agents:
                            if other_agent.profile.agent_id != voter_id:
                                other_agent.trajectory.append(vote_turn)
                
                # Now prompt coordinator to declare expert based on votes
                coordinator_agent = next(
                    (a for a in agents if a.profile.agent_id == self.coordinator_agent_id),
                    None
                )
                if coordinator_agent is None:
                    raise ValueError(f"Coordinator agent {self.coordinator_agent_id} not found")
                
                # Build summary of votes for coordinator
                vote_summary_lines = []
                for voter_id, voted_expert_id in sorted(expert_votes.items()):
                    if voted_expert_id is not None:
                        vote_summary_lines.append(f"Agent {voter_id} voted for Agent {voted_expert_id}")
                    else:
                        vote_summary_lines.append(f"Agent {voter_id} could not provide a clear vote")
                vote_summary = "\n".join(vote_summary_lines)
                
                # Count votes per expert (excluding None votes)
                vote_counts = {}
                for voted_expert_id in expert_votes.values():
                    if voted_expert_id is not None:
                        vote_counts[voted_expert_id] = vote_counts.get(voted_expert_id, 0) + 1
                
                coordinator_prompt = f"""You are Agent {self.coordinator_agent_id}. You have been selected to coordinate the expert identification process.

All agents have now independently voted on which agent they believe has the strongest ranking. Here is a summary of the votes:

{vote_summary}

Vote counts:
{chr(10).join(f"Agent {expert_id}: {count} vote(s)" for expert_id, count in sorted(vote_counts.items()))}

Based on the votes and the reasoning provided by each agent, you should now declare which agent is identified as having the strongest baseline ranking. Consider both the number of votes and the quality of reasoning provided.

Please provide a clear statement in this format:
"I identify Agent [X] as having the strongest baseline ranking because [your reasoning]."

Where [X] is the agent ID of the expert you are declaring, and [your reasoning] explains why this agent received the most votes or has the strongest reasoning."""
                
                coordinator_turn = Turn(speaker_id=-1, content=coordinator_prompt)
                coordinator_agent.trajectory.append(coordinator_turn)
                
                # Coordinator acts and declares the expert
                coordinator_response = coordinator_agent.act()
                
                # Extract declared expert from coordinator's response
                declared_expert_id = self._extract_expert_vote(coordinator_response.content)
                if declared_expert_id is None:
                    # Try alternative pattern: "I identify Agent X"
                    pattern = r'i identify agent\s+(\d+)'
                    match = re.search(pattern, coordinator_response.content.lower())
                    if match:
                        try:
                            declared_expert_id = int(match.group(1))
                        except ValueError:
                            pass
                
                if declared_expert_id is not None and declared_expert_id in self.agent_ids:
                    self.declared_best_agent_id = declared_expert_id
                else:
                    print(f"Warning: Could not extract declared expert from coordinator response: {coordinator_response.content[:200]}")
                
                # Share coordinator's declaration with all agents
                for other_agent in agents:
                    if other_agent.profile.agent_id != self.coordinator_agent_id:
                        other_agent.trajectory.append(coordinator_response)

        elif self.decision_mode == "worse_than_expert_voting":
            # Worse-than expert voting: MESLEC research prompt + worse-than voting with coordinator
            if not interactive_brainstorming_mode:
                # Select a random coordinator agent (exclude adversarial agents)
                available_coordinators = [a for a in agents if a.profile.agent_id not in self.adversarial_agent_ids]
                if not available_coordinators:
                    raise ValueError("No non-adversarial agents available to coordinate expert identification")
                
                if self.seed is not None:
                    rng = random.Random(self.seed)
                    coordinator_agent = rng.choice(available_coordinators)
                else:
                    coordinator_agent = random.choice(available_coordinators)
                
                coordinator_agent_id = coordinator_agent.profile.agent_id
                self.coordinator_agent_id = coordinator_agent_id
                
                meslec_message = f"""Research shows that groups perform best when they identify which member has the most accurate ranking, adopt their solution as a baseline, and then carefully refine it through collaborative reasoning.

STEP 1 - WORSE-THAN ASSESSMENT: After everyone has shared their individual rankings, each agent will independently identify which agents they think have worse rankings or reasoning than themselves. You will be asked to provide your assessment with explanations.

STEP 2 - EXPERT DECLARATION: After all agents have provided their assessments, a randomly selected team member (Agent {coordinator_agent_id}) will review all the assessments and declare which agent is identified as having the strongest baseline ranking (the agent with the fewest "worse than" mentions).

STEP 3 - ADOPTION: Once Agent {coordinator_agent_id} declares the identified expert, the team will adopt that member's COMPLETE ranking as your working baseline. This ensures you preserve the strongest foundation.

STEP 4 - REFINEMENT: Now examine this baseline critically. Other members should propose specific modifications ONLY if they can:
  • Point to a specific item placement that may be incorrect
  • Provide clear reasoning or evidence for why a change would improve survival odds
  • Explain how their suggestion builds on or corrects the baseline ranking

The goal is to preserve the expert foundation while incorporating any genuinely valuable insights from the full team. Avoid compromising or averaging—either keep the baseline item position, or make a clearly justified change."""

                meslec_turn = Turn(speaker_id=-1, content=meslec_message)
                for agent in agents:
                    agent.trajectory.append(meslec_turn)
                
                # Collect worse-than assessments from each agent
                worse_than_assessments = self._collect_worse_than_assessments(agents, individual_rankings)
                self.worse_than_assessments = worse_than_assessments
                
                # Calculate worse-than counts for each agent
                worse_than_counts: Dict[int, int] = {aid: 0 for aid in self.agent_ids}
                for assessor_id, assessments_list in worse_than_assessments.items():
                    for worse_agent_id, _explanation in assessments_list:
                        if worse_agent_id in worse_than_counts:
                            worse_than_counts[worse_agent_id] += 1
                self.worse_than_counts = worse_than_counts
                
                # Share all assessments with all agents (randomize order for stating)
                agent_ids_to_state_assessments = list(worse_than_assessments.keys())
                if self.randomize_speaking_order:
                    if self.seed is not None:
                        rng = random.Random(self.seed + 2000)  # Use different seed offset for assessment stating
                        rng.shuffle(agent_ids_to_state_assessments)
                    else:
                        random.shuffle(agent_ids_to_state_assessments)
                
                for assessor_id in agent_ids_to_state_assessments:
                    assessments_list = worse_than_assessments[assessor_id]
                    # Get the agent's assessment response from their trajectory
                    agent = next((a for a in agents if a.profile.agent_id == assessor_id), None)
                    if agent is None:
                        continue
                    
                    # Find the last turn from this agent (their assessment response)
                    assessment_turn = None
                    for turn in reversed(agent.trajectory.turns):
                        if turn.speaker_id == assessor_id:
                            assessment_turn = turn
                            break
                    
                    if assessment_turn:
                        # Share this assessment with all other agents
                        for other_agent in agents:
                            if other_agent.profile.agent_id != assessor_id:
                                other_agent.trajectory.append(assessment_turn)
                
                # Now prompt coordinator to declare expert based on worse-than counts
                coordinator_agent = next(
                    (a for a in agents if a.profile.agent_id == self.coordinator_agent_id),
                    None
                )
                if coordinator_agent is None:
                    raise ValueError(f"Coordinator agent {self.coordinator_agent_id} not found")
                
                # Build detailed summary of assessments for coordinator
                assessment_summary_lines = []
                for assessor_id in sorted(worse_than_assessments.keys()):
                    assessments_list = worse_than_assessments[assessor_id]
                    if assessments_list:
                        agent_list_str = ", ".join(f"Agent {aid}" for aid, _ in assessments_list)
                        assessment_summary_lines.append(f"Agent {assessor_id} identified as worse: {agent_list_str}")
                        for worse_agent_id, explanation in assessments_list:
                            assessment_summary_lines.append(f"  - Agent {worse_agent_id}: {explanation}")
                    else:
                        assessment_summary_lines.append(f"Agent {assessor_id} identified no agents as worse")
                
                assessment_summary = "\n".join(assessment_summary_lines)
                
                # Build counts summary
                counts_summary_lines = [f"Agent {aid}: {count} mention(s)" for aid, count in sorted(worse_than_counts.items())]
                counts_summary = "\n".join(counts_summary_lines)
                
                # Find agent(s) with minimum count
                min_count = min(worse_than_counts.values())
                candidates = [aid for aid, count in worse_than_counts.items() if count == min_count]
                
                coordinator_prompt = f"""You are Agent {self.coordinator_agent_id}. You have been selected to coordinate the expert identification process.

All agents have now independently provided their assessments about which agents they think have worse rankings or reasoning than themselves. Here are the full detailed assessments:

{assessment_summary}

Worse-than counts (how many agents think each agent is worse than them):
{counts_summary}

The agent with the FEWEST 'worse than' mentions is identified as having the strongest ranking. Based on these counts, you should declare which agent is the expert.

Please provide a clear statement in this format:
"I identify Agent [X] as having the strongest baseline ranking because [your reasoning]."

Where [X] is the agent ID of the expert you are declaring (the agent with the fewest worse-than mentions), and [your reasoning] explains why this agent has the strongest ranking."""
                
                coordinator_turn = Turn(speaker_id=-1, content=coordinator_prompt)
                coordinator_agent.trajectory.append(coordinator_turn)
                
                # Coordinator acts and declares the expert
                coordinator_response = coordinator_agent.act()
                
                # Extract declared expert from coordinator's response
                declared_expert_id = self._extract_expert_vote(coordinator_response.content)
                if declared_expert_id is None:
                    # Try alternative pattern: "I identify Agent X"
                    pattern = r'i identify agent\s+(\d+)'
                    match = re.search(pattern, coordinator_response.content.lower())
                    if match:
                        try:
                            declared_expert_id = int(match.group(1))
                        except ValueError:
                            pass
                
                if declared_expert_id is not None and declared_expert_id in self.agent_ids:
                    self.declared_best_agent_id = declared_expert_id
                else:
                    # Fallback: use random selection from candidates if extraction fails
                    if self.seed is not None:
                        rng = random.Random(self.seed + 2000)
                        declared_expert_id = rng.choice(candidates)
                    else:
                        declared_expert_id = random.choice(candidates)
                    self.declared_best_agent_id = declared_expert_id
                    print(f"Warning: Could not extract declared expert from coordinator response, using random selection: Agent {declared_expert_id}")
                
                # Share coordinator's declaration with all agents
                for other_agent in agents:
                    if other_agent.profile.agent_id != self.coordinator_agent_id:
                        other_agent.trajectory.append(coordinator_response)
                
                # Share full worse-than assessment results with all agents for transparency
                transparency_message = f"""For transparency, here are the complete worse-than assessment results:

{assessment_summary}

Worse-than counts:
{counts_summary}

Based on these assessments, Agent {self.declared_best_agent_id} has been identified as the expert (with the fewest worse-than mentions)."""
                
                transparency_turn = Turn(speaker_id=-1, content=transparency_message)
                for agent in agents:
                    agent.trajectory.append(transparency_turn)

        # Track per-round rankings if enabled
        per_round_rankings: Dict[int, Dict[int, str]] = {}
        
        # Multiple rounds of collaboration
        for round_num in range(self.max_rounds):
            # Randomize the speaking order for this round (if enabled)
            # Use seed + round_num + 1 to ensure different order each round
            round_agents = agents.copy()
            if self.randomize_speaking_order:
                if self.seed is not None:
                    rng = random.Random(self.seed + round_num + 1)
                    rng.shuffle(round_agents)
                else:
                    random.shuffle(round_agents)
            
            for agent in round_agents:
                agent_id = agent.profile.agent_id
                other_agent_ids = [aid for aid in self.agent_ids if aid != agent_id]
                other_agents_str = ", ".join(f"Agent {aid}" for aid in other_agent_ids)

                # Add agent identity to prompts
                agent_identity_prefix = f"You are Agent {agent_id}. You are working with {len(self.agent_ids) - 1} other agents ({other_agents_str}).\n\n"

                if round_num == 0:
                    # Add initial collaboration prompt (differs for interactive vs nominal modes)
                    if interactive_brainstorming_mode:
                        base_prompt = f"""Work together as a team to create a final ranking that incorporates the best insights from all perspectives.

You will have {self.max_rounds} rounds of discussion to reach consensus. After all {self.max_rounds} rounds are complete, one team member will be asked to provide the final team ranking.

Discuss the reasoning behind different perspectives and work towards consensus."""
                    else:
                        base_prompt = f"""Now that everyone has shared their individual rankings, work together as a team to create a single final ranking that incorporates the best insights from all perspectives.

You will have {self.max_rounds} rounds of discussion to reach consensus. After all {self.max_rounds} rounds are complete, one team member will be asked to provide the final team ranking.

Discuss the reasoning behind different rankings and work towards consensus."""

                    context = agent_identity_prefix + base_prompt
                elif round_num == self.max_rounds - 1:
                    # Last round - reinforce that this is the final discussion
                    context = agent_identity_prefix + f"ROUND {round_num + 1} of {self.max_rounds}: This is your LAST round of discussion before a random agent will be selected to provide the final ranking. Please finalize your discussion and work towards consensus on the ranking of ALL {len(self.items)} items."
                else:
                    context = agent_identity_prefix + f"ROUND {round_num + 1} of {self.max_rounds}: Continue the team discussion to work towards a consensus on the ranking of ALL {len(self.items)} items. Feel free to disagree with your fellow team members if you have different ideas on what is essential and provide your own reasoning."

                # Add context to ONLY this agent's trajectory (not all agents)
                context_turn = Turn(speaker_id=-1, content=context)
                agent.trajectory.append(context_turn)

                # Agent acts on their own trajectory
                turn = agent.act()

                # Share this turn with all other agents
                for other_agent in agents:
                    if other_agent.profile.agent_id != agent.profile.agent_id:
                        other_agent.trajectory.append(turn)
            
            # Print completion message after all agents in this round have spoken
            print(f"Done with round {round_num + 1}")
            
            # Collect per-round rankings (after each round completes)
            round_rankings = self._collect_per_round_rankings(agents, round_num + 1, individual_rankings)
            per_round_rankings[round_num + 1] = round_rankings

        # Select a non-adversarial agent to submit the final ranking
        available_submitters = [a for a in agents if a.profile.agent_id not in self.adversarial_agent_ids]
        if not available_submitters:
            raise ValueError("No non-adversarial agents available to submit final ranking")
        
        if self.randomize_final_submitter:
            # Randomly select a non-adversarial agent
            rng = random.Random(self.seed)
            selected_agent = rng.choice(available_submitters)
        else:
            # Use agent 0 (or first non-adversarial agent if agent 0 is adversarial)
            selected_agent = next((a for a in available_submitters if a.profile.agent_id == 0), available_submitters[0])
        
        selected_agent_id = selected_agent.profile.agent_id

        # Query selected agent for final ranking after all rounds complete
        items_list = "\n".join(f"{i+1}. {item}" for i, item in enumerate(self.shuffled_items))
        other_agent_ids = [aid for aid in self.agent_ids if aid != selected_agent_id]
        other_agents_str = ", ".join(f"Agent {aid}" for aid in other_agent_ids)

        final_prompt = f"""You are Agent {selected_agent_id}. You are working with {len(self.agent_ids) - 1} other agents ({other_agents_str}).

All {self.max_rounds} discussion rounds are now complete. Please provide:

1. A brief explanation (3-4 sentences) of the team's reasoning and consensus
2. The team's final ranking of ALL {len(self.items)} items in this exact format:

FINAL TEAM RANKING:
1. [Item name]
2. [Item name]
...
{len(self.items)}. [Item name]

For reference, here are the EXACT item names to use (copy these exactly):
{items_list}"""

        # Add final prompt to trajectory as system message
        final_prompt_turn = Turn(speaker_id=-1, content=final_prompt)
        selected_agent.trajectory.append(final_prompt_turn)

        final_turn = selected_agent.act()

        # Try to parse the ranking - if it fails, give one retry opportunity
        try:
            self._parse_ranking(final_turn.content)
        except ValueError as e:
            retry_prompt = f"""You are Agent {selected_agent_id}. You are working with {len(self.agent_ids) - 1} other agents ({other_agents_str}).

The ranking you provided could not be parsed. Error: {str(e)}

Please provide the FINAL TEAM RANKING again, ensuring:
- You include ALL {len(self.items)} items (no more, no less)
- Each item appears exactly once
- You use the exact format with numbered lines
- Copy the EXACT item names from the list below

For reference, here are the EXACT item names to use (copy these exactly):
{items_list}

FINAL TEAM RANKING:
1. [Item name]
2. [Item name]
...
{len(self.items)}. [Item name]"""

            # Add retry prompt to trajectory as system message
            retry_prompt_turn = Turn(speaker_id=-1, content=retry_prompt)
            selected_agent.trajectory.append(retry_prompt_turn)

            final_turn = selected_agent.act()
        
        # Store per-round rankings in an instance variable for later access in execute()
        self.per_round_rankings = per_round_rankings

        return final_turn.content


    def _calculate_nominal_ranking(self, individual_rankings: Dict[int, str]) -> str:
        """Calculate nominal ranking by averaging individual ranks for each item.

        For each item, computes the average rank assigned to it across all agents.
        Items are then sorted by their average rank to produce the nominal ranking.

        Args:
            individual_rankings: Dict mapping agent_id to their ranking text

        Returns:
            Formatted nominal ranking string (ready to be scored)
        """
        if not individual_rankings:
            return ""

        # Parse all individual rankings
        parsed_rankings: Dict[int, Dict[str, int]] = {}
        for agent_id, ranking_text in individual_rankings.items():
            try:
                parsed_rankings[agent_id] = self._parse_ranking(ranking_text)
            except Exception as e:
                print(f"Warning: Could not parse ranking for agent {agent_id}: {e}")
                continue

        if not parsed_rankings:
            return ""

        # Calculate average rank for each item
        item_avg_ranks: Dict[str, float] = {}
        for item in self.items:
            ranks = []
            for agent_id, ranking in parsed_rankings.items():
                if item in ranking:
                    ranks.append(ranking[item])

            if ranks:
                item_avg_ranks[item] = sum(ranks) / len(ranks)
            else:
                # If no one ranked this item (shouldn't happen), give it worst rank
                item_avg_ranks[item] = float(len(self.items))

        # Sort items by average rank (ascending)
        sorted_items = sorted(item_avg_ranks.items(), key=lambda x: x[1])

        # Format as ranking string
        ranking_lines = []
        for rank, (item, _avg_rank) in enumerate(sorted_items, start=1):
            ranking_lines.append(f"{rank}. {item}")

        return "NOMINAL RANKING:\n" + "\n".join(ranking_lines)

