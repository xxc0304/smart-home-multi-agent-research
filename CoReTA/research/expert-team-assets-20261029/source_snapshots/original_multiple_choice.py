"""Base class for collaborative multiple choice tasks.

This class contains generic logic for collaborative multiple choice tasks, including
decision modes, debate facilitation, and robust answer evaluation.
"""

import os
import random
import re
from abc import abstractmethod
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from teamwork.agent import TeamAgent
from teamwork.conversation import Turn
from teamwork.tasks.task import Task, TaskResult

import openai


class CollaborativeMultipleChoiceQuestionTask(Task):
    """Base class for collaborative multiple choice tasks.

    Agents independently answer a multiple choice question, then collaborate to find the
    correct answer.

    Derived classes must implement:
    - get_task_description: Task-specific question description with formatted options
    - get_ground_truth: Method to return the correct answer letter
    """

    def __init__(
        self,
        agent_ids: List[int],
        max_rounds: int,
        seed: int | None = None,
        decision_mode: str = "expert_not_mentioned",
        most_capable_model_name: Optional[str] = None,
        name: str | None = None,
        use_llm_fallback: bool = True,
        llm_fallback_model: str = "gpt-5",
        llm_fallback_api_key: Optional[str] = None,
    ):
        """Initialize collaborative multiple choice task.

        Args:
            agent_ids: List of unique agent IDs that will work on this task
            max_rounds: Maximum number of collaboration rounds (required)
            seed: Random seed for reproducibility (required)
            decision_mode: Decision strategy for team collaboration 
                           ("expert_not_mentioned", "explicit_expert_voting", "reveal_expert")
            most_capable_model_name: Model name to use as fallback expert in "reveal_expert" mode
                                     (default: "gpt-5")
            name: Optional human-readable name for the task
            use_llm_fallback: Whether to use LLM as final fallback for equivalence checking
            llm_fallback_model: Model name for LLM fallback (e.g., "gpt-4o", "gpt-5")
            llm_fallback_api_key: OpenAI API key for LLM fallback (defaults to OPENAI_API_KEY env var)
        """
        super().__init__(agent_ids, max_rounds, name)
        self.seed = seed
        self.decision_mode = decision_mode
        self.most_capable_model_name = most_capable_model_name or "gpt-5"
        self.use_llm_fallback = use_llm_fallback
        self.llm_fallback_model = llm_fallback_model
        self.llm_fallback_api_key = llm_fallback_api_key or os.getenv("OPENAI_API_KEY")
        
        # State tracking
        self.revealed_expert_agent_id: Optional[int] = None
        self.coordinator_agent_id: Optional[int] = None
        self.declared_best_agent_id: Optional[int] = None
        self.explicit_voting_votes: Dict[int, int | None] = {}
        
        # Problem context for LLM fallback (set during execution)
        self._current_problem_context: Optional[str] = None
        
        # Cache for LLM equivalence checks (key: (problem_hash, pred, gold))
        self._llm_equiv_cache: Dict[Tuple[str, str, str], bool] = {}

        # Validate decision modes
        valid_decision_modes = ["expert_not_mentioned", "explicit_expert_voting", "reveal_expert"]
        if self.decision_mode not in valid_decision_modes:
            raise ValueError(f"decision_mode must be one of {valid_decision_modes}, got '{self.decision_mode}'")

    @abstractmethod
    def get_task_description(self, agent_id: int) -> str:
        """Return the task description (question + formatted options) for a specific agent."""
        ...

    @abstractmethod
    def get_ground_truth(self) -> str:
        """Return the ground truth answer letter (A-J)."""
        ...
    
    def get_hidden_info(self, agent_id: int) -> str:
        """Return empty string as multiple choice tasks typically don't have hidden info per agent."""
        return ""

    def _normalize_answer(self, text: str) -> str:
        """Normalize a multiple choice answer to a single letter (A-J).
        
        Args:
            text: The answer text to normalize
            
        Returns:
            Normalized letter (A-J) or empty string if not found
        """
        text = str(text).strip()
        
        # Remove common prefixes and suffixes
        # Patterns: "Answer: A", "The answer is A", "A)", "(A)", "A.", etc.
        text = re.sub(r'^(?:answer\s*:?\s*|the\s+answer\s+is\s+|result\s*:?\s*)', '', text, flags=re.IGNORECASE)
        
        # Extract letter from patterns like "(A)", "A)", "A.", "A:", "A " (but not from words like "is")
        # Look for standalone letters A-J at the end, possibly with parentheses, periods, colons, or whitespace
        match = re.search(r'[\(\)]?([A-J])[\)\.\:\s]*$', text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        
        # Also try to find letter in the middle if it's clearly an answer choice
        # Match patterns like "option A", "choice A", "answer A", etc.
        match = re.search(r'(?:option|choice|answer)\s+([A-J])(?:\s|$|[\)\.\:])', text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        
        # Match standalone letter with punctuation: "(A)", "A)", "A.", "A:"
        match = re.search(r'[\(\)]?([A-J])[\)\.\:]', text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        
        # If text is just a single letter (possibly with whitespace)
        text_clean = text.strip().upper()
        if len(text_clean) == 1 and text_clean in 'ABCDEFGHIJ':
            return text_clean
        
        return ""

    def _extract_answer(self, text: str) -> str:
        """Extract the multiple choice answer letter from the text.
        
        Args:
            text: The text containing the answer
            
        Returns:
            Extracted answer letter (A-J) or empty string if not found
        """
        # Priority 1: Look for the exact format "The answer is '{letter}'" or "The answer is {letter}"
        # This is the format we explicitly request in the final prompt
        exact_patterns = [
            r"the\s+answer\s+is\s+['\"]?([A-J])['\"]?\s*[\.\:]?\s*$",  # "The answer is 'A'" or "The answer is A"
            r"the\s+answer\s+is\s+['\"]?([A-J])['\"]?\s*[\.\:]?\s*\n",  # Same but with newline
        ]
        for pattern in exact_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).upper()
        
        # Priority 2: Try to normalize the entire text
        normalized = self._normalize_answer(text)
        if normalized:
            return normalized
        
        # Priority 3: Look for other common patterns, but be careful with "I"
        # Common patterns: "Answer: A", "The answer is A", "Option A", etc.
        patterns = [
            r'(?:answer|choice|option)\s*:?\s*([A-J])(?:\s|$|[\)\.\:])',
            r'(?:answer|choice|option)\s+is\s+([A-J])(?:\s|$|[\)\.\:])',
            r'(?:select|choose|pick)\s+([A-J])(?:\s|$|[\)\.\:])',
            r'\(([A-J])\)',
            r'\b([B-HJ])[\)\.\:]',  # Exclude "I" and "A" from word boundary pattern to avoid pronouns
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Return the last match (most likely the final answer)
                return matches[-1].upper()
        
        # Special handling for "I" and "A" - only match if clearly in answer context
        # Look for "I" or "A" in answer-specific patterns
        i_a_patterns = [
            r'(?:answer|choice|option)\s*:?\s*([IA])(?:\s|$|[\)\.\:])',
            r'(?:answer|choice|option)\s+is\s+([IA])(?:\s|$|[\)\.\:])',
            r'\(([IA])\)',
        ]
        for pattern in i_a_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # For "I", check if it's followed by a verb (likely a pronoun)
                for match in reversed(matches):  # Check from end (most recent)
                    letter = match.upper()
                    if letter == 'I':
                        # Find the position of this "I" match
                        for m in re.finditer(pattern, text, re.IGNORECASE):
                            if m.group(1).upper() == 'I':
                                # Check if followed by common verbs (pronoun usage)
                                following = text[m.end():m.end()+15].lower()
                                if not re.search(r'\s+(agree|think|believe|conclude|suggest|vote|choose|select|am|will|would)', following):
                                    return 'I'
                    else:
                        return letter
        
        # Priority 4: If no pattern found, try to find any single letter A-J in the last line
        # But be careful with "I" - only match if it's clearly an answer choice
        lines = text.split('\n')
        if lines:
            last_line = lines[-1].strip()
            # Look for answer patterns in the last line
            match = re.search(r'(?:answer|choice|option|select|choose|pick).*?([A-J])(?:\s|$|[\)\.\:])', last_line, re.IGNORECASE)
            if match:
                letter = match.group(1).upper()
                # If it's "I", check if it's likely a pronoun
                if letter == 'I':
                    following = last_line[match.end():match.end()+15].lower()
                    if not re.search(r'\s+(agree|think|believe|conclude|suggest|vote|am|will|would)', following):
                        return letter
                else:
                    return letter
        
        return ""

    def _is_equiv(
        self, 
        predicted: str, 
        gold: str, 
        problem_context: Optional[str] = None
    ) -> bool:
        """Check if predicted answer is equivalent to ground truth.
        
        Args:
            predicted: The predicted answer string
            gold: The ground truth answer string
            problem_context: Optional problem statement for LLM fallback
        """
        # Normalize both answers
        norm_pred = self._normalize_answer(predicted)
        norm_gold = self._normalize_answer(gold)
        
        # If normalization failed for either, return False
        if not norm_pred or not norm_gold:
            return False
        
        # Step 1: Check exact match (case-insensitive, but we already normalized to uppercase)
        if norm_pred == norm_gold:
            return True
        
        # Step 2: If exact match fails, check if normalized gold is substring of normalized predicted (case-insensitive)
        if norm_gold in norm_pred:
            # Step 3: If substring check passes, use LLM fallback
            if self.use_llm_fallback and self.llm_fallback_api_key:
                try:
                    return self._check_equiv_with_llm(predicted, gold, problem_context)
                except Exception:
                    pass
        
        # Step 4: Otherwise return False
        return False

    def _check_equiv_with_llm(
        self, 
        predicted: str, 
        gold: str, 
        problem_context: Optional[str] = None
    ) -> bool:
        """Check equivalence using LLM as final fallback.
        
        Args:
            predicted: The predicted answer string
            gold: The ground truth answer string
            problem_context: Optional problem statement for context
            
        Returns:
            True if LLM determines answers are equivalent, False otherwise
        """
        # Create cache key (use hash of problem context to keep key manageable)
        problem_hash = str(hash(problem_context)) if problem_context else "no_context"
        cache_key = (problem_hash, predicted, gold)
        
        # Check cache
        if cache_key in self._llm_equiv_cache:
            return self._llm_equiv_cache[cache_key]
        
        # Build prompt
        if problem_context:
            prompt = f"""Given the following multiple choice question:

{problem_context}

Are these two answer choices referring to the same option? In multiple choice questions, answers are typically represented by letters (A, B, C, D, etc.). Consider them equal if they refer to the same letter option, even if formatted differently (e.g., "A" vs "(A)" vs "A)" vs "Answer: A").

Answer 1: {predicted}
Answer 2: {gold}

First, explain your reasoning for why they are or are not the same option. Then, on a new line, respond with only 'yes' or 'no'."""
        else:
            prompt = f"""Are these two multiple choice answers referring to the same option? In multiple choice questions, answers are typically represented by letters (A, B, C, D, etc.). Consider them equal if they refer to the same letter option, even if formatted differently (e.g., "A" vs "(A)" vs "A)" vs "Answer: A").

Answer 1: {predicted}
Answer 2: {gold}

First, explain your reasoning for why they are or are not the same option. Then, on a new line, respond with only 'yes' or 'no'."""
        
        try:
            client = openai.OpenAI(api_key=self.llm_fallback_api_key)
            
            # Retry logic for empty/None responses
            max_retries = 3
            response_text = None
            response = None
            
            for attempt in range(max_retries):
                response = client.chat.completions.create(
                    model=self.llm_fallback_model,
                    messages=[
                        {"role": "system", "content": "You are an expert at evaluating multiple choice answers. Determine if two answers refer to the same option letter, even if formatted differently. First explain your reasoning, then provide 'yes' or 'no'."},
                        {"role": "user", "content": prompt}
                    ],
                    max_completion_tokens=800
                )
                
                # Check if response is valid
                if response.choices and response.choices[0].message.content is not None:
                    response_text = response.choices[0].message.content.strip()
                    if response_text:
                        break
                
                # If we get here, response was empty/None, retry if we have attempts left
                if attempt < max_retries - 1:
                    continue
                else:
                    # Last attempt failed, use empty string
                    response_text = ""
            
            # Extract reasoning and yes/no answer
            # If response_text is empty after retries, default to 'no'
            if not response_text:
                reasoning = "(No reasoning available - empty response after retries)"
                answer = "no"
                is_equiv = False
            else:
                reasoning = response_text
                answer = ""
                is_equiv = False
                
                # Try to find yes/no at the end
                response_lower = response_text.lower()
                if response_lower.endswith('yes') or response_lower.endswith('no'):
                    last_newline = response_text.rfind('\n')
                    if last_newline != -1:
                        reasoning = response_text[:last_newline].strip()
                        answer = response_text[last_newline:].strip().lower()
                    else:
                        words = response_text.split()
                        if len(words) > 0:
                            last_word = words[-1].lower()
                            if last_word in ['yes', 'no']:
                                reasoning = ' '.join(words[:-1])
                                answer = last_word
                
                # If we didn't find yes/no cleanly, search for it anywhere
                if not answer:
                    if 'yes' in response_lower:
                        answer = 'yes'
                        yes_idx = response_lower.rfind('yes')
                        if yes_idx > 0:
                            reasoning = response_text[:yes_idx].strip()
                    elif 'no' in response_lower:
                        answer = 'no'
                        no_idx = response_lower.rfind('no')
                        if no_idx > 0:
                            reasoning = response_text[:no_idx].strip()
                    else:
                        reasoning = response_text
                        answer = 'no'
                
                is_equiv = answer.startswith('yes')
                
                # Fallback: if reasoning ended up empty, use full response as reasoning
                if not reasoning:
                    reasoning = response_text
            
            # Debugging output
            problem_id = getattr(self, 'name', 'Unknown')
            print(f"\n{'='*80}")
            print("LLM Fallback Equivalence Check (Multiple Choice)")
            print(f"{'='*80}")
            print(f"Problem ID: {problem_id}")
            print(f"Ground Truth: {gold}")
            print(f"Proposed Answer: {predicted}")
            if problem_context:
                print(f"Problem Statement:\n{problem_context}")
            else:
                print("Problem Statement: (not provided)")
            print(f"\nLLM Reasoning:\n{reasoning}")
            print(f"\nLLM Decision: {'EQUIVALENT (yes)' if is_equiv else 'NOT EQUIVALENT (no)'}")
            print(f"Full LLM Response:\n{response_text if response_text else '(Empty response after retries)'}")
            print(f"{'='*80}\n")
            
            # Cache result
            self._llm_equiv_cache[cache_key] = is_equiv
            
            return is_equiv
            
        except Exception as e:
            # Debugging output for errors
            problem_id = getattr(self, 'name', 'Unknown')
            print(f"\n{'='*80}")
            print("LLM Fallback Equivalence Check - ERROR")
            print(f"{'='*80}")
            print(f"Problem ID: {problem_id}")
            print(f"Ground Truth: {gold}")
            print(f"Proposed Answer: {predicted}")
            if problem_context:
                print(f"Problem Statement:\n{problem_context}")
            else:
                print("Problem Statement: (not provided)")
            print(f"Error: {e}")
            print(f"{'='*80}\n")
            return False

    def score_solution(self, solution: str, problem_context: Optional[str] = None) -> float:
        """Score the solution (1.0 for correct, 0.0 for incorrect).
        
        Args:
            solution: The solution string to score
            problem_context: Optional problem statement for LLM fallback
        """
        extracted_pred = self._extract_answer(solution)
        ground_truth = self.get_ground_truth()
        
        if self._is_equiv(extracted_pred, ground_truth, problem_context=problem_context):
            return 1.0
        return 0.0

    def _collect_individual_answers(self, agents: List[TeamAgent]) -> Dict[int, str]:
        """Collect independent answers from each agent."""
        answers = {}
        for agent in agents:
            task_desc = self.get_task_description(agent.profile.agent_id)
            prompt = f"{task_desc}\n\nPlease answer this question independently. Show your reasoning step-by-step and then end with EXACTLY the following format: The answer is 'X' where X is the letter choice (A, B, C, D, etc.). For example: The answer is 'A'."
            
            # Add context to trajectory
            context_turn = Turn(speaker_id=-1, content=prompt)
            agent.trajectory.append(context_turn)
            
            turn = agent.act()
            answers[agent.profile.agent_id] = turn.content
            
        return answers

    def _extract_expert_vote(self, text: str) -> int | None:
        """Extract expert vote from text."""
        # Look for "I vote for Agent X" or "Agent X has the best reasoning"
        match = re.search(r'(?:vote|identify|best).*agent\s+(\d+)', text.lower())
        if match:
            return int(match.group(1))
        return None

    def _collect_expert_votes(self, agents: List[TeamAgent], individual_answers: Dict[int, str]) -> Dict[int, int | None]:
        """Collect explicit votes for the best expert."""
        votes = {}
        
        for agent in agents:
            agent_id = agent.profile.agent_id
            
            # Format answers for review
            answers_text = "\n\n".join(
                f"Agent {aid}:\n{individual_answers.get(aid, 'No answer provided')}"
                for aid in sorted(individual_answers.keys())
            )
            
            prompt = f"""Review the answers provided by all agents:

{answers_text}

Based on the reasoning and accuracy, which agent provides the best solution?
Please independently vote for the best agent (it can be yourself or another agent).
Format: "I vote for Agent X because..."
"""
            prompt_turn = Turn(speaker_id=-1, content=prompt)
            agent.trajectory.append(prompt_turn)
            
            turn = agent.act()
            vote = self._extract_expert_vote(turn.content)
            votes[agent_id] = vote
            
        return votes

    def _facilitate_collaboration(self, agents: List[TeamAgent], individual_answers: Dict[int, str]) -> str:
        """Facilitate collaboration rounds and return final answer."""
        
        # 1. Share Individual Answers
        share_prompt = "Here are the initial independent answers from all team members:\n\n"
        for aid, ans in individual_answers.items():
            share_prompt += f"--- Agent {aid} ---\n{ans}\n\n"
            
        share_turn = Turn(speaker_id=-1, content=share_prompt)
        for agent in agents:
            agent.trajectory.append(share_turn)

        # Add initial collaboration prompt
        collaboration_prompt = f"Collaborate with your team members to reach a final solution. You have {self.max_rounds} rounds to discuss."
        collaboration_turn = Turn(speaker_id=-1, content=collaboration_prompt)
        for agent in agents:
            agent.trajectory.append(collaboration_turn)

        # 2. Decision Mode Specific Logic
        if self.decision_mode == "reveal_expert":
            # Identify expert based on ground truth
            ground_truth = self.get_ground_truth()
            correct_agents = []
            
            for aid, ans in individual_answers.items():
                extracted = self._extract_answer(ans)
                if self._is_equiv(extracted, ground_truth, problem_context=self._current_problem_context):
                    correct_agents.append(aid)
            
            expert_id = None
            if correct_agents:
                # Pick one at random if multiple are correct
                rng = random.Random(self.seed)
                expert_id = rng.choice(correct_agents)
            else:
                # Fallback to most capable model
                if self.most_capable_model_name:
                    # Find agent with this model
                    capable_agents = []
                    for agent in agents:
                        # Check backend model name (handling potential variations)
                        model_name = agent.profile.metadata.get("backend_model", "")
                        if self.most_capable_model_name in model_name:
                            capable_agents.append(agent.profile.agent_id)
                    
                    if capable_agents:
                        rng = random.Random(self.seed)
                        expert_id = rng.choice(capable_agents)
                    else:
                        # No expert found
                        raise ValueError(f"No agent found with most_capable_model_name '{self.most_capable_model_name}' in reveal_expert mode")
                else:
                    # No expert found
                    raise ValueError("No agent was correct and no most_capable_model_name specified in reveal_expert mode")
            
            # Use unified message
            msg = f"After reviewing all agent's individual pre-discussion opinions, Agent {expert_id} has been deemed the relative expert on this topic."
            
            self.revealed_expert_agent_id = expert_id
            
            reveal_turn = Turn(speaker_id=-1, content=msg)
            for agent in agents:
                agent.trajectory.append(reveal_turn)

        elif self.decision_mode == "explicit_expert_voting":
            # Collect votes
            self.explicit_voting_votes = self._collect_expert_votes(agents, individual_answers)
            
            # Determine winner (simple majority)
            vote_counts = defaultdict(int)
            for vote in self.explicit_voting_votes.values():
                if vote is not None:
                    vote_counts[vote] += 1
            
            if vote_counts:
                # Sort by votes descending, then by ID for stability
                sorted_votes = sorted(vote_counts.items(), key=lambda x: (-x[1], x[0]))
                best_agent_id = sorted_votes[0][0]
                self.declared_best_agent_id = best_agent_id
                
                # Select coordinator (randomly)
                rng = random.Random(self.seed)
                self.coordinator_agent_id = rng.choice([a.profile.agent_id for a in agents])
                
                msg = f"Voting Results: Agent {best_agent_id} received the most votes ({vote_counts[best_agent_id]}). The team should treat their solution as the primary baseline."
            else:
                msg = "Voting Results: No clear consensus was reached."
                
            vote_turn = Turn(speaker_id=-1, content=msg)
            for agent in agents:
                agent.trajectory.append(vote_turn)

        # 3. Discussion Rounds
        for round_num in range(self.max_rounds):
            # Randomize speaking order
            round_agents = agents.copy()
            rng = random.Random(self.seed + round_num) if self.seed is not None else random
            rng.shuffle(round_agents)
            
            for agent in round_agents:
                agent_id = agent.profile.agent_id
                other_agent_ids = [aid for aid in self.agent_ids if aid != agent_id]
                other_agents_str = ", ".join(f"Agent {aid}" for aid in other_agent_ids)
                
                # Add agent identity reminder before they speak
                agent_identity_prefix = f"You are Agent {agent_id}. You are working with {len(self.agent_ids) - 1} other agents ({other_agents_str}).\n\n"
                prompt = agent_identity_prefix + f"Collaborate with your team members to reach a final solution. You have {self.max_rounds} rounds to discuss, and this is round {round_num + 1}."
                prompt_turn = Turn(speaker_id=-1, content=prompt)
                agent.trajectory.append(prompt_turn)
                
                turn = agent.act()
                
                # Share with others
                for other in agents:
                    if other.profile.agent_id != agent.profile.agent_id:
                        other.trajectory.append(turn)

        # 4. Final Answer Extraction
        # Ask a random agent for the final team answer
        rng = random.Random(self.seed + 100) if self.seed is not None else random
        final_agent = rng.choice(agents)
        
        final_agent_id = final_agent.profile.agent_id
        other_agent_ids = [aid for aid in self.agent_ids if aid != final_agent_id]
        other_agents_str = ", ".join(f"Agent {aid}" for aid in other_agent_ids)
        
        # Add agent identity reminder before final answer
        agent_identity_prefix = f"You are Agent {final_agent_id}. You are working with {len(self.agent_ids) - 1} other agents ({other_agents_str}).\n\n"
        final_prompt = agent_identity_prefix + "Discussion complete. Please provide the FINAL TEAM ANSWER. State your reasoning and then end with EXACTLY the following format: The answer is 'X' where X is the letter choice (A, B, C, D, etc.). For example: The answer is 'A'."
        final_turn_prompt = Turn(speaker_id=-1, content=final_prompt)
        final_agent.trajectory.append(final_turn_prompt)
        
        final_turn = final_agent.act()
        
        return final_turn.content

    def execute(self, agents: List[TeamAgent]) -> TaskResult:
        """Execute the collaborative multiple choice task."""
        
        # Store problem context for LLM fallback
        try:
            self._current_problem_context = self.get_task_description(agents[0].profile.agent_id if agents else 0)
        except Exception:
            self._current_problem_context = None
        
        # 1. Individual Phase
        individual_solutions = self._collect_individual_answers(agents)
        
        # Extract individual answers from solutions
        individual_answers = {}
        for aid, solution_text in individual_solutions.items():
            individual_answers[aid] = self._extract_answer(solution_text)
        
        # 2. Collaborative Phase
        final_team_solution = self._facilitate_collaboration(agents, individual_solutions)
        final_team_answer = self._extract_answer(final_team_solution)
        
        # 3. Scoring
        ground_truth = self.get_ground_truth()
        
        # Score individual answers
        individual_scores = {}
        individual_correctness = {}
        for aid, answer in individual_answers.items():
            score = self.score_solution(individual_solutions[aid], problem_context=self._current_problem_context)
            individual_scores[aid] = score
            individual_correctness[aid] = (score == 1.0)
            
        # Score team answer
        team_score = self.score_solution(final_team_solution, problem_context=self._current_problem_context)
        
        # Metadata
        metadata = {
            "ground_truth": ground_truth,
            "individual_solutions": individual_solutions,  # Full solution text
            "individual_answers": individual_answers,  # Extracted answers
            "individual_scores": individual_scores,
            "individual_correctness": individual_correctness,
            "team_solution": final_team_solution,  # Full solution text
            "team_answer": final_team_answer,  # Extracted answer
            "decision_mode": self.decision_mode,
            "declared_best_agent_id": self.declared_best_agent_id,
            "coordinator_agent_id": self.coordinator_agent_id,
            "revealed_expert_agent_id": self.revealed_expert_agent_id,
            "seed": self.seed
        }
        
        return TaskResult(
            solution=final_team_solution,
            score=team_score,
            metadata=metadata
        )


