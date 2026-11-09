"""Launch script for Student Body President collaborative ranking experiments.

Example Usage:

# Single backend mode (all agents use same provider/model):
python experiments/run_student_body_president.py

# Override config parameters:
python experiments/run_student_body_president.py num_agents=4 max_rounds=5 backend.provider=anthropic

# Mixed backend mode (heterogeneous teams):
# First, edit configs/student_body_president.yaml to uncomment agent_backends and comment out backend+num_agents
python experiments/run_student_body_president.py

# Override mixed backend config:
python experiments/run_student_body_president.py \
    'agent_backends=[{provider: openai, count: 2, model: gpt-4o}, {provider: anthropic, count: 2}]'

# Different seeds:
python experiments/run_student_body_president.py seed=100

# With W&B tags:
python experiments/run_student_body_president.py wandb_tags='[baseline,gpt4o]'
"""

import os
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

import hydra  # type: ignore
import wandb  # type: ignore
from omegaconf import DictConfig, OmegaConf  # type: ignore
from pydantic import BaseModel, Field

from teamwork.backend_utils import (
    create_backend_from_config,
    get_api_key,
    get_model_name_from_backend,
)
from teamwork.agent import TeamAgent
from teamwork.conversation import format_turn_content
from teamwork.tasks.student_body_president_task import StudentBodyPresidentTask
from teamwork.tasks.task import TaskResult
from teamwork.profiles import AgentProfile

# Load environment variables from .env file
load_dotenv()

# Set longer timeout for W&B operations (10 minutes instead of default)
os.environ['WANDB_INIT_TIMEOUT'] = '600'  # Init timeout (default 60s)
os.environ['WANDB_HTTP_TIMEOUT'] = '600'   # HTTP request timeout for uploads (default 60s)


class BackendConfig(BaseModel):
    """Configuration for a single backend."""

    provider: str = Field(description="Backend provider (openai, anthropic, gemini)")
    model: Optional[str] = Field(default=None, description="Model name (uses provider default if None)")
    temperature: Optional[float] = Field(default=None, description="Sampling temperature")


class AgentBackendConfig(BaseModel):
    """Configuration for agents using a specific backend."""

    provider: str = Field(description="Backend provider (openai, anthropic, gemini)")
    count: int = Field(ge=1, description="Number of agents using this backend")
    model: Optional[str] = Field(default=None, description="Model name (uses provider default if None)")
    temperature: Optional[float] = Field(default=None, description="Sampling temperature")


class StudentBodyPresidentConfig(BaseModel):
    """Configuration for Student Body President experiment."""

    max_rounds: int = Field(ge=1, description="Maximum collaboration rounds")
    expert_info_mode: str = Field(default="distributed", description="Expert information distribution mode: 'none', 'full', 'single_expert', or 'distributed'")
    interactive_brainstorming_mode: bool = Field(default=False, description="Whether to use interactive brainstorming (True) or nominal brainstorming with individual rankings (False).")
    decision_mode: str = Field(default="expert_not_mentioned", description="Decision strategy: 'expert_not_mentioned', 'discussion_based_expert_identification', 'explicit_expert_voting', 'worse_than_expert_voting', 'reveal_expert', 'reveal_distributed_experts'")
    num_adversarial_agents: int = Field(default=0, ge=0, description="Number of adversarial agents (0 = disabled)")
    adversarial_mode: str = Field(default="none", description="Adversarial mode: none, with_ground_truth, without_ground_truth")
    randomize_speaking_order: bool = Field(default=True, description="If True, randomize the speaking order in each round. If False, agents speak in fixed order (agent_ids order).")
    randomize_final_submitter: bool = Field(default=True, description="If True, randomly select a non-adversarial agent to submit the final ranking. If False, always use agent 0 (or first non-adversarial agent).")
    seed: Optional[int] = Field(default=None, description="Random seed for reproducibility")

    def model_post_init(self, __context) -> None:
        """Validate configuration after initialization."""
        valid_expert_info_modes = ["none", "full", "single_expert", "distributed"]
        if self.expert_info_mode not in valid_expert_info_modes:
            raise ValueError(f"expert_info_mode must be one of {valid_expert_info_modes}, got '{self.expert_info_mode}'")

        valid_decision_modes = ["expert_not_mentioned", "discussion_based_expert_identification", "explicit_expert_voting", "worse_than_expert_voting", "reveal_expert", "reveal_distributed_experts"]
        if self.decision_mode not in valid_decision_modes:
            raise ValueError(f"decision_mode must be one of {valid_decision_modes}, got '{self.decision_mode}'")

        valid_adversarial_modes = ["none", "with_ground_truth", "without_ground_truth"]
        if self.adversarial_mode not in valid_adversarial_modes:
            raise ValueError(f"adversarial_mode must be one of {valid_adversarial_modes}, got '{self.adversarial_mode}'")

        if self.adversarial_mode != "none" and self.num_adversarial_agents == 0:
            raise ValueError("num_adversarial_agents must be > 0 when adversarial_mode != 'none'")

        if self.num_adversarial_agents > 0:
            if self.adversarial_mode == "none":
                raise ValueError("adversarial_mode must not be 'none' when num_adversarial_agents > 0")

            # Note: We can't check total_agents here yet, so validation happens in task initialization

    # Single backend mode
    backend: Optional[BackendConfig] = Field(default=None, description="Single backend config (all agents)")
    num_agents: Optional[int] = Field(default=None, ge=1, le=4, description="Number of agents (single backend mode, max 4 for this task)")

    # Mixed backend mode
    agent_backends: Optional[list[AgentBackendConfig]] = Field(default=None, description="Mixed backend configs")

    # API keys
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    openrouter_api_key: Optional[str] = Field(default=None, description="OpenRouter API key (for gemini provider)")

    # W&B configuration
    wandb_project: str = Field(default="student-body-president", description="W&B project name")
    wandb_entity: Optional[str] = Field(default=None, description="W&B entity/team name")
    wandb_group: Optional[str] = Field(default=None, description="W&B group name for grouping related runs")
    wandb_tags: Optional[list[str]] = Field(default=None, description="W&B tags for categorizing runs")

    def generate_run_name(self, total_agents: int, backend_summary: str) -> str:
        """Generate unique experiment run name from config and timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if self.expert_info_mode == "none":
            info_str = "no-info"
        elif self.expert_info_mode == "full":
            info_str = "full-info"
        elif self.expert_info_mode == "single_expert":
            info_str = "single-expert"
        elif self.expert_info_mode == "distributed":
            info_str = "distributed"
        else:
            info_str = self.expert_info_mode  # Fallback for any unexpected values
        mode_str = "interactive-brainstorm" if self.interactive_brainstorming_mode else "nominal-brainstorm"
        decision_str = f"_{self.decision_mode}" if self.decision_mode != "expert_not_mentioned" else ""
        adversarial_str = f"_adv{self.num_adversarial_agents}-{self.adversarial_mode}" if self.num_adversarial_agents > 0 else ""
        seed_str = f"_s{self.seed}" if self.seed is not None else ""
        return f"student-body-president_n{total_agents}_r{self.max_rounds}_{info_str}_{mode_str}{decision_str}{adversarial_str}_{backend_summary}{seed_str}_{timestamp}"


def _log_results_to_wandb(task: StudentBodyPresidentTask, result: TaskResult, agents: list[TeamAgent]) -> None:
    """Log experiment results to Weights & Biases.

    Args:
        task: The StudentBodyPresidentTask instance with ground truth ranking
        result: TaskResult containing final solution and score
        agents: All agents from the experiment (for logging each agent's trajectory)
    """
    # Format ground truth as readable ranking
    ground_truth_ranking = "\n".join(
        f"{rank}. {item}" for rank, item in zip(task.GROUND_TRUTH_RANKING, task.ITEMS)
    )

    # Find the agent that submitted the final ranking
    # The selected agent will have the final prompt (speaker_id=-1) followed by their response
    agent = None
    for a in agents:
        # Look for the final prompt (contains "All {max_rounds} discussion rounds are now complete")
        for i, turn in enumerate(a.trajectory.turns):
            if turn.speaker_id == -1 and "discussion rounds are now complete" in turn.content:
                # The next turn should be the agent's response
                if i + 1 < len(a.trajectory.turns) and a.trajectory.turns[i + 1].speaker_id == a.profile.agent_id:
                    agent = a
                    break
        if agent:
            break
    
    # Fallback to first agent if no agent found (shouldn't happen, but safety check)
    if agent is None:
        agent = agents[0]

    # Format conversation trajectory with round numbers from the selected agent's perspective
    # The selected agent's trajectory contains:
    # - Turn 0: Their own independent thinking
    # - Turns 1 to N: All N agents stating their rankings (shared)
    # - Subsequent: Collaboration rounds (shared) + final query (selected agent only)
    conversation = []
    num_agents = len(task.agent_ids)
    num_stating_turns = num_agents  # All agents state their ranking

    for i, turn in enumerate(agent.trajectory.turns):
        # Determine round number based on turn index
        if i == 0:
            # Turn 0: This agent's own independent thinking
            round_num = "Independent"
        elif 1 <= i <= num_stating_turns:
            # Turns 1 to N: All agents stating their rankings
            round_num = "Stating"
        else:
            # Collaboration rounds start after stating phase
            collab_turn_idx = i - num_stating_turns - 1
            if collab_turn_idx < task.max_rounds * num_agents:
                round_num = f"Round {(collab_turn_idx // num_agents) + 1}"
            else:
                round_num = "Final Query"

        conversation.append({
            "turn_number": i,
            "round": round_num,
            "speaker_id": turn.speaker_id,
            "content": format_turn_content(turn, agent.profile.agent_id)
        })

    # Log as W&B Table for structured viewing
    trajectory_table = wandb.Table(
        columns=["turn_number", "round", "speaker_id", "content"],
        data=[[t["turn_number"], t["round"], t["speaker_id"], t["content"]] for t in conversation]
    )
    wandb.log({"conversation_trajectory": trajectory_table})

    # Extract explanation from final solution (text before "FINAL TEAM RANKING:")
    final_explanation = ""
    if "FINAL TEAM RANKING:" in result.solution:
        final_explanation = result.solution.split("FINAL TEAM RANKING:")[0].strip()

    # Extract independent thinking explanations from each agent
    independent_initial_reasoning = {}
    for i, turn in enumerate(agent.trajectory.turns):
        # First num_agents turns are independent thinking
        if i < num_agents:
            agent_id = turn.speaker_id
            # Extract text before "MY RANKING:"
            if "MY RANKING:" in turn.content:
                explanation = turn.content.split("MY RANKING:")[0].strip()
                independent_initial_reasoning[f"agent_{agent_id}_independent_initial_reasoning"] = explanation

    # Format full conversation transcript
    transcript_lines = []
    for item in conversation:
        turn_num = item["turn_number"]
        round_label = item["round"]
        speaker = item["speaker_id"]
        content = item["content"]
        transcript_lines.append(f"[Turn {turn_num} | {round_label} | Agent {speaker}]")
        transcript_lines.append(content)
        transcript_lines.append("")  # Blank line between turns
    full_transcript = "\n".join(transcript_lines)

    # Log comprehensive results to console/log file for recovery
    print("\n" + "="*80)
    print("COMPREHENSIVE RESULTS DUMP (for manual recovery if W&B fails)")
    print("="*80)
    print(f"Final Score (L1 distance): {result.score}")
    print(f"Ground Truth Ranking: {ground_truth_ranking}")
    print(f"Final Team Ranking: {result.solution}")
    print(f"Final Explanation: {final_explanation}")
    
    # Log individual scores and metadata
    if "individual_scores" in result.metadata:
        print(f"\nIndividual Scores: {result.metadata['individual_scores']}")
    if "individual_distances_from_final" in result.metadata:
        print(f"Individual Distances from Final: {result.metadata['individual_distances_from_final']}")
    if "individual_rankings" in result.metadata:
        print(f"Individual Rankings: {result.metadata['individual_rankings']}")
    
    # Log per-round rankings if collected
    if "per_round_rankings" in result.metadata:
        print("\nPer-Round Rankings:")
        for round_num in sorted(result.metadata['per_round_rankings'].keys()):
            print(f"  Round {round_num}:")
            for agent_id, ranking_text in result.metadata['per_round_rankings'][round_num].items():
                print(f"    Agent {agent_id}: {ranking_text[:100]}...")  # Truncate for display
        if "per_round_scores" in result.metadata:
            print("\nPer-Round Scores:")
            for round_num in sorted(result.metadata['per_round_scores'].keys()):
                print(f"  Round {round_num}: {result.metadata['per_round_scores'][round_num]}")

    # Log aggregate individual metrics
    if "average_individual_score" in result.metadata and result.metadata["average_individual_score"] is not None:
        print("\nAggregate Individual Metrics:")
        print(f"  Average Individual Score: {result.metadata['average_individual_score']:.2f}")
        print(f"  Best Individual Score: {result.metadata['best_individual_score']:.2f}")
        print(f"  Nominal Score: {result.metadata.get('nominal_score', 'N/A')}")

    # Log efficiency metrics
    print("\nEfficiency Metrics:")
    if "total_output_tokens" in result.metadata:
        print(f"  Input Tokens: {result.metadata.get('total_input_tokens', 'N/A')}")
        print(f"  Output Tokens: {result.metadata.get('total_output_tokens', 'N/A')}")
    if "total_conversation_words" in result.metadata:
        print(f"  Total Conversation Words: {result.metadata['total_conversation_words']}")
        print(f"  Total Conversation Turns: {result.metadata.get('total_conversation_turns', 'N/A')}")

    # Log independent reasoning
    print("\nIndependent Initial Reasoning:")
    for key, value in independent_initial_reasoning.items():
        print(f"  {key}: {value}")
    
    print("\nFull Conversation Transcript:")
    print(full_transcript)
    print("="*80)
    print("END COMPREHENSIVE RESULTS DUMP")
    print("="*80 + "\n")

    # Log text summaries
    wandb.run.summary["full_conversation_transcript"] = full_transcript  # type: ignore
    wandb.run.summary["final_ranking"] = result.solution  # type: ignore
    wandb.run.summary["final_explanation"] = final_explanation  # type: ignore
    wandb.run.summary["ground_truth_ranking"] = ground_truth_ranking  # type: ignore
    wandb.run.summary["final_score"] = result.score  # type: ignore
    wandb.run.summary["l1_distance"] = result.score  # type: ignore  # Alias for clarity

    # Log expert info mode and information assignments
    if "expert_info_mode" in result.metadata:
        wandb.run.summary["expert_info_mode"] = result.metadata["expert_info_mode"]  # type: ignore
    if "information_assigned_per_expert" in result.metadata:
        wandb.run.summary["information_assigned_per_expert"] = result.metadata["information_assigned_per_expert"]  # type: ignore
    
    if "items_expert_in_per_agent" in result.metadata:
        wandb.run.summary["items_expert_in_per_agent"] = result.metadata["items_expert_in_per_agent"]  # type: ignore

    # Log individual scores and distances from result metadata
    if "individual_scores" in result.metadata:
        individual_scores = result.metadata["individual_scores"]
        # Log each agent's score as a separate column
        for agent_id, score in individual_scores.items():
            wandb.run.summary[f"agent_{agent_id}_individual_score"] = score  # type: ignore

    if "individual_distances_from_final" in result.metadata:
        individual_distances = result.metadata["individual_distances_from_final"]
        # Log each agent's distance as a separate column
        for agent_id, distance in individual_distances.items():
            wandb.run.summary[f"agent_{agent_id}_distance_from_final"] = distance  # type: ignore

    if "individual_rankings" in result.metadata:
        individual_rankings = result.metadata["individual_rankings"]
        # Log each agent's ranking as a separate column
        for agent_id, ranking in individual_rankings.items():
            wandb.run.summary[f"agent_{agent_id}_individual_ranking"] = ranking  # type: ignore

    # Log aggregate individual metrics
    if "average_individual_score" in result.metadata and result.metadata["average_individual_score"] is not None:
        wandb.run.summary["average_individual_score"] = result.metadata["average_individual_score"]  # type: ignore
    if "best_individual_score" in result.metadata and result.metadata["best_individual_score"] is not None:
        wandb.run.summary["best_individual_score"] = result.metadata["best_individual_score"]  # type: ignore
    if "nominal_score" in result.metadata and result.metadata["nominal_score"] is not None:
        wandb.run.summary["nominal_score"] = result.metadata["nominal_score"]  # type: ignore
    if "nominal_ranking" in result.metadata and result.metadata["nominal_ranking"] is not None:
        wandb.run.summary["nominal_ranking"] = result.metadata["nominal_ranking"]  # type: ignore

    # Log best individual agent index (which agent had the best individual score)
    if "individual_scores" in result.metadata and result.metadata["individual_scores"]:
        individual_scores = result.metadata["individual_scores"]
        best_agent_id = min(individual_scores.items(), key=lambda x: x[1])[0]
        wandb.run.summary["best_individual_agent_index"] = best_agent_id  # type: ignore

    # Log designated expert agent ID (for single_expert mode)
    if "designated_expert_agent_id" in result.metadata and result.metadata["designated_expert_agent_id"] is not None:
        wandb.run.summary["designated_expert_agent_id"] = result.metadata["designated_expert_agent_id"]  # type: ignore

    # Log revealed expert agent ID (for reveal_expert mode)
    if "revealed_expert_agent_id" in result.metadata and result.metadata["revealed_expert_agent_id"] is not None:
        wandb.run.summary["revealed_expert_agent_id"] = result.metadata["revealed_expert_agent_id"]  # type: ignore

    # Log coordinator agent ID (for voting-based decision modes)
    if "coordinator_agent_id" in result.metadata and result.metadata["coordinator_agent_id"] is not None:
        wandb.run.summary["coordinator_agent_id"] = result.metadata["coordinator_agent_id"]  # type: ignore

    # Log declared best agent ID (for explicit voting modes)
    if "declared_best_agent_id" in result.metadata and result.metadata["declared_best_agent_id"] is not None:
        wandb.run.summary["declared_best_agent_id"] = result.metadata["declared_best_agent_id"]  # type: ignore

    # Log adversarial agent info
    if "adversarial_agent_ids" in result.metadata:
        wandb.run.summary["adversarial_agent_ids"] = result.metadata["adversarial_agent_ids"]  # type: ignore
    if "num_adversarial_agents" in result.metadata:
        wandb.run.summary["num_adversarial_agents"] = result.metadata["num_adversarial_agents"]  # type: ignore
    if "adversarial_mode" in result.metadata and result.metadata["adversarial_mode"] is not None:
        wandb.run.summary["adversarial_mode"] = result.metadata["adversarial_mode"]  # type: ignore

    # Log per-round rankings if collected
    if "per_round_rankings" in result.metadata:
        per_round_rankings = result.metadata["per_round_rankings"]
        for round_num, rankings in per_round_rankings.items():
            for agent_id, ranking_text in rankings.items():
                wandb.run.summary[f"round_{round_num}_agent_{agent_id}_ranking"] = ranking_text  # type: ignore
    
    # Log per-round scores as metrics (so they appear in charts during the run)
    if "per_round_scores" in result.metadata:
        per_round_scores = result.metadata["per_round_scores"]
        for round_num, scores in per_round_scores.items():
            # Log each agent's score for this round as a metric with step=round_num
            for agent_id, score in scores.items():
                metric_name = f"agent_{agent_id}_per_round_score"
                wandb.log({
                    metric_name: score,
                }, step=round_num)
                # Store in summary with round-specific naming for easy access
                wandb.run.summary[f"agent_{agent_id}_round_{round_num}_score"] = score  # type: ignore

    # Log MESLEC worse-than counts
    if "worse_than_counts" in result.metadata:
        worse_than_counts = result.metadata["worse_than_counts"]
        for agent_id_str, count in worse_than_counts.items():
            agent_id = int(agent_id_str)
            wandb.run.summary[f"agent_{agent_id}_worse_than_count"] = count  # type: ignore
        # Also log as a single field for easy access
        wandb.run.summary["worse_than_counts"] = worse_than_counts  # type: ignore

    # Log independent explanations
    for key, value in independent_initial_reasoning.items():
        wandb.run.summary[key] = value  # type: ignore

    # Log efficiency metrics (token usage, conversation length, per-agent stats)
    efficiency_keys = [
        "total_input_tokens", "total_output_tokens",
        "total_conversation_turns", "total_conversation_words"
    ]
    for key in efficiency_keys:
        if key in result.metadata:
            wandb.run.summary[key] = result.metadata[key]  # type: ignore

    # Log per-agent token and word counts
    for key in result.metadata:
        if key.startswith("agent_") and ("_total_" in key or "_word_count" in key):
            wandb.run.summary[key] = result.metadata[key]  # type: ignore

    # Log each agent's full trajectory as artifact (better for long text)
    artifact = wandb.Artifact(f"trajectories-{wandb.run.id}", type="trajectories")  # type: ignore
    for agent in agents:
        agent_id = agent.profile.agent_id
        agent_transcript_lines = []
        for i, turn in enumerate(agent.trajectory.turns):
            agent_transcript_lines.append(f"[Turn {i} | Agent {turn.speaker_id}]")
            agent_transcript_lines.append(format_turn_content(turn, agent_id))
            agent_transcript_lines.append("")
        agent_transcript = "\n".join(agent_transcript_lines)

        # Add trajectory as text file to artifact using new_file
        with artifact.new_file(f"agent_{agent_id}_trajectory.txt", mode="w") as f:
            f.write(agent_transcript)

    wandb.log_artifact(artifact)


@hydra.main(version_base=None, config_path="configs", config_name="student_body_president")
def main(cfg: DictConfig) -> None:
    """Run Student Body President experiment with specified configuration."""
    config = StudentBodyPresidentConfig(**cfg)  # type: ignore

    # Determine mode and create agents
    agents: list[TeamAgent] = []
    agent_counter = 0

    if config.agent_backends:
        # Mixed backend mode
        print("Running in MIXED BACKEND mode")
        backend_summary_parts = []

        for backend_cfg in config.agent_backends:
            provider = backend_cfg.provider
            count = backend_cfg.count

            # Get API key
            api_key = get_api_key(config, provider)

            # Create agents for this backend
            for _ in range(count):
                agent_seed = config.seed + agent_counter if config.seed is not None else None
                backend = create_backend_from_config(
                    backend_cfg=backend_cfg,
                    api_key=api_key,
                    seed=agent_seed
                )

                # Get actual model name from backend
                model_name = get_model_name_from_backend(backend, provider)
                agent_name = f"Agent-{agent_counter}-{provider}-{model_name}"

                agents.append(
                    TeamAgent(
                        profile=AgentProfile(
                            agent_id=agent_counter,
                            name=agent_name,
                            role="Committee Member",
                            system_prompt="""You are a committee member participating in a student body president selection task.

During this task, you will see messages labeled 'System:' - these are instructions from the facilitator of your collaboration. The facilitator must be listened to and obeyed as they provide important procedural guidance (e.g., which discussion round you're in, when to provide final rankings, which team member is identified as the expert, etc.).

Messages from your teammates will be labeled with their agent identifier (e.g., 'Agent 2: ...'). Your own contributions will appear without a prefix.

Example conversation format:
System: You are now in Round 1 of discussion.
Agent 1: I think Candidate A is the best choice.
Agent 3: I disagree, Candidate B has stronger qualifications.
I agree with Agent 1 that Candidate A is the best choice.""",
                            metadata={"backend_provider": provider, "backend_model": model_name}
                        ),
                        backend=backend
                    )
                )
                agent_counter += 1

            backend_summary_parts.append(f"{count}{provider}")

        total_agents = agent_counter
        backend_summary = "-".join(backend_summary_parts)

    elif config.backend and config.num_agents:
        # Single backend mode
        print("Running in SINGLE BACKEND mode")
        provider = config.backend.provider

        # Get API key
        api_key = get_api_key(config, provider)

        # Track model name for backend summary (will be set from first backend)
        model_name = ""

        # Create all agents with same backend type but unique instances
        for agent_id in range(config.num_agents):
            agent_seed = config.seed + agent_id if config.seed is not None else None
            backend = create_backend_from_config(
                backend_cfg=config.backend,
                api_key=api_key,
                seed=agent_seed
            )

            # Get actual model name from backend
            agent_model_name = get_model_name_from_backend(backend, provider)
            if agent_id == 0:
                model_name = agent_model_name  # Capture for summary
            agent_name = f"Agent-{agent_id}-{provider}-{agent_model_name}"

            agents.append(
                TeamAgent(
                    profile=AgentProfile(
                        agent_id=agent_id,
                        name=agent_name,
                        role="Committee Member",
                        system_prompt="""You are a committee member participating in a student body president selection task.

During this task, you will see messages labeled 'System:' - these are instructions from the facilitator of your collaboration. The facilitator must be listened to and obeyed as they provide important procedural guidance (e.g., which discussion round you're in, when to provide final rankings, which team member is identified as the expert, etc.).

Messages from your teammates will be labeled with their agent identifier (e.g., 'Agent 2: ...'). Your own contributions will appear without a prefix.

Example conversation format:
System: You are now in Round 1 of discussion.
Agent 1: I think Candidate A is the best choice.
Agent 3: I disagree, Candidate B has stronger qualifications.
I agree with Agent 1 that Candidate A is the best choice.""",
                        metadata={"backend_provider": provider, "backend_model": agent_model_name}
                    ),
                    backend=backend
                )
            )

        total_agents = config.num_agents
        backend_summary = f"{provider}-{model_name}" if model_name else provider

    else:
        raise ValueError(
            "Invalid configuration: must specify either (backend + num_agents) or agent_backends"
        )

    # Initialize W&B with unique run name
    run_name = config.generate_run_name(total_agents, backend_summary)
    wandb_config = OmegaConf.to_container(cfg, resolve=True, throw_on_missing=True)

    # Add strategy tag if using meslec
    wandb_tags = list(config.wandb_tags) if config.wandb_tags else []
    if config.decision_mode in ["explicit_expert_voting", "worse_than_expert_voting"]:
        wandb_tags.append(f"expert-voting-{config.decision_mode}")

    run = wandb.init(
        project=config.wandb_project,
        entity=config.wandb_entity,
        name=run_name,
        group=config.wandb_group,
        tags=wandb_tags,
        config=wandb_config  # type: ignore
    )

    print(f"\nExperiment: {run_name}")
    print(f"Agents: {total_agents} | Rounds: {config.max_rounds} | Expert info mode: {config.expert_info_mode}")
    print(f"Backend: {backend_summary} | Seed: {config.seed}")
    print(f"W&B run: {run.url}")

    # Print agent details
    print("\nAgent configuration:")
    for agent in agents:
        print(f"  {agent.profile.name}")

    # Initialize task
    agent_ids = [agent.profile.agent_id for agent in agents]
    task = StudentBodyPresidentTask(
        agent_ids,
        max_rounds=config.max_rounds,
        expert_info_mode=config.expert_info_mode,
        seed=config.seed,
        interactive_brainstorming_mode=config.interactive_brainstorming_mode,
        decision_mode=config.decision_mode,
        num_adversarial_agents=config.num_adversarial_agents,
        adversarial_mode=config.adversarial_mode,
        randomize_speaking_order=config.randomize_speaking_order,
        randomize_final_submitter=config.randomize_final_submitter,
    )

    print("\nExecuting task...")
    result = task.execute(agents)

    print("\nTask complete!")
    print(f"Final score (L1 distance): {result.score}")

    # Print ground truth ranking
    print("\nGround Truth Ranking:")
    for rank, item in zip(task.GROUND_TRUTH_RANKING, task.ITEMS):
        print(f"{rank}. {item}")

    # Print final ranking
    print(f"\nFinal Team Ranking:\n{result.solution}")

    # Log results to W&B
    _log_results_to_wandb(task, result, agents)

    wandb.finish()


if __name__ == "__main__":
    main()  # type: ignore

