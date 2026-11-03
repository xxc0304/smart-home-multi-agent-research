"""Launch script for GPQA Diamond collaborative experiments."""

import os
import random
import statistics
from datetime import datetime
from typing import Any, Dict, List, Optional

import hydra
import wandb
from datasets import load_dataset
from dotenv import load_dotenv
from omegaconf import DictConfig, OmegaConf
from pydantic import BaseModel, Field

from teamwork.backend_utils import (
    build_backend_summary,
    create_backend_from_config,
    get_api_key,
    get_model_name_from_backend,
    sanitize_model_name_for_summary,
)
from teamwork.agent import TeamAgent
from teamwork.profiles import AgentProfile
from teamwork.tasks.gpqa_diamond_problem_task import GPQADiamondProblemTask

# Load environment variables
load_dotenv()


def get_question_ids_from_run(run_name: str, project: str = "gpqa-diamond-teamwork", entity: Optional[str] = None) -> List[int]:
    """Retrieve question_ids from a W&B run's history.
    
    Args:
        run_name: Name of the W&B run to retrieve question_ids from
        project: W&B project name
        entity: W&B entity/team name (optional)
        
    Returns:
        List of question_ids (as integers) from the run
    """
    api = wandb.Api()
    
    # Search for the run by name (not by ID/path)
    print(f"Searching for run with name: '{run_name}' in project '{project}' (entity: {entity or 'default'})...")
    
    # Construct project path for searching
    if entity:
        project_path = f"{entity}/{project}"
    else:
        project_path = project
        # Try to detect entity from wandb settings
        try:
            settings = wandb.Settings()
            if hasattr(settings, 'entity') and settings.entity:
                detected_entity = settings.entity
                project_path = f"{detected_entity}/{project}"
                print(f"Using detected entity: {detected_entity}")
        except Exception:
            pass
    
    try:
        # Get all runs from the project
        all_runs = api.runs(project_path)
        
        # Find run with matching name
        matching_run = None
        for r in all_runs:
            if r.name == run_name:
                matching_run = r
                break
        
        if matching_run is None:
            # Try partial match or show similar runs
            similar_runs = []
            for r in all_runs:
                if run_name in r.name or r.name.startswith(run_name[:50]) or run_name[:50] in r.name:
                    similar_runs.append(r)
            
            error_msg = f"Could not find run with name '{run_name}' in project '{project_path}'"
            if similar_runs:
                error_msg += f"\nFound {len(similar_runs)} runs with similar names:"
                for r in similar_runs[:5]:
                    error_msg += f"\n  - {r.name} (ID: {r.id})"
            else:
                error_msg += f"\nNo runs found with similar names. Total runs in project: {len(list(all_runs))}"
            raise ValueError(error_msg)
        
        run = matching_run
        print(f"Found run: {run.name} (ID: {run.id})")
        
        # Get full history (all logged steps)
        history = run.history()
        
        if 'question_id' not in history.columns:
            raise ValueError(f"Run {run_name} does not contain 'question_id' in history")
        
        # Extract unique question_ids and convert to integers
        question_ids = history['question_id'].dropna().unique().tolist()
        question_ids = [int(qid) for qid in question_ids if str(qid).strip()]
        
        print(f"Found {len(question_ids)} unique question_ids in reference run")
        return sorted(question_ids)
        
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Failed to search for run '{run_name}' in project '{project_path}': {e}")

# Set longer timeout for W&B operations
os.environ['WANDB_INIT_TIMEOUT'] = '600'
os.environ['WANDB_HTTP_TIMEOUT'] = '600'


class BackendConfig(BaseModel):
    """Configuration for a single backend."""
    provider: str = Field(description="Backend provider (openai, anthropic, gemini)")
    model: Optional[str] = Field(default=None, description="Model name")
    temperature: Optional[float] = Field(default=None, description="Sampling temperature")


class AgentBackendConfig(BaseModel):
    """Configuration for agents using a specific backend."""
    provider: str = Field(description="Backend provider (openai, anthropic, gemini)")
    count: int = Field(ge=1, description="Number of agents using this backend")
    model: Optional[str] = Field(default=None, description="Model name")
    temperature: Optional[float] = Field(default=None, description="Sampling temperature")


class GPQADiamondConfig(BaseModel):
    """Configuration for GPQA Diamond experiment."""
    
    dataset_name: str = Field(default="fingertap/GPQA-Diamond", description="Dataset name")
    limit: Optional[int] = Field(default=None, description="Limit number of problems (for testing)")
    reference_run_name: Optional[str] = Field(default=None, description="W&B run name to retrieve question_ids from (filters dataset to same subset)")
    
    max_rounds: int = Field(ge=1, description="Maximum collaboration rounds")
    
    def model_post_init(self, __context) -> None:
        """Validate configuration after initialization."""
        # Ensure only one of limit or reference_run_name is specified
        if self.limit is not None and self.reference_run_name is not None:
            raise ValueError(
                "Cannot specify both 'limit' and 'reference_run_name'. "
                "Use 'limit' for random sampling or 'reference_run_name' to filter by question_ids from a reference run."
            )
    num_agents: Optional[int] = Field(default=None, ge=1, description="Number of agents (single backend mode)")
    
    decision_mode: str = Field(default="expert_not_mentioned", description="Decision strategy")
    most_capable_model_name: Optional[str] = Field(default="o4-mini-2025-04-16", description="Fallback expert model name")
    
    # LLM Fallback for Answer Equivalence
    use_llm_fallback: bool = Field(default=True, description="Use LLM as final fallback for equivalence checking")
    llm_fallback_model: str = Field(default="gpt-5-2025-08-07", description="Model name for LLM fallback (e.g., 'gpt-4o', 'gpt-5-2025-08-07')")
    llm_fallback_api_key: Optional[str] = Field(default=None, description="API key for LLM fallback (defaults to OPENAI_API_KEY)")
    
    seed: int = Field(default=42, description="Random seed")
    
    # Backends
    backend: Optional[BackendConfig] = Field(default=None, description="Single backend config")
    agent_backends: Optional[List[AgentBackendConfig]] = Field(default=None, description="Mixed backend configs")
    
    # API Keys
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    openrouter_api_key: Optional[str] = Field(default=None, description="OpenRouter API key (for gemini provider)")
    
    # W&B
    wandb_project: str = Field(default="gpqa-diamond-teamwork", description="W&B project name")
    wandb_entity: Optional[str] = Field(default=None, description="W&B entity/team name")
    wandb_group: Optional[str] = Field(default=None, description="W&B group name")
    wandb_tags: Optional[List[str]] = Field(default=None, description="W&B tags")

    def generate_run_name(self, total_agents: int, backend_summary: str, num_problems: int) -> str:
        """Generate unique experiment run name."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        decision_str = f"_{self.decision_mode}" if self.decision_mode != "expert_not_mentioned" else ""
        seed_str = f"_s{self.seed}" if self.seed is not None else ""
        problems_str = f"p{num_problems}"
        return f"gpqadiamond_{problems_str}_n{total_agents}_r{self.max_rounds}{decision_str}_{backend_summary}{seed_str}_{timestamp}"


@hydra.main(version_base=None, config_path="configs", config_name="gpqa_diamond")
def main(cfg: DictConfig) -> None:
    """Run GPQA Diamond experiment."""
    config = GPQADiamondConfig(**cfg)

    # 1. Initialize Agents
    agents: List[TeamAgent] = []
    agent_counter = 0
    backend_summary = ""
    
    if config.agent_backends:
        # Mixed backend mode
        print("Running in MIXED BACKEND mode")
        
        for backend_cfg in config.agent_backends:
            provider = backend_cfg.provider
            count = backend_cfg.count
            
            api_key = get_api_key(config, provider)
            
            for _ in range(count):
                agent_seed = config.seed + agent_counter
                backend = create_backend_from_config(
                    backend_cfg=backend_cfg,
                    api_key=api_key,
                    seed=agent_seed
                )
                model_name = get_model_name_from_backend(backend, provider)
                agent_name = f"Agent-{agent_counter}-{provider}-{model_name}"
                
                agents.append(TeamAgent(
                    profile=AgentProfile(
                        agent_id=agent_counter,
                        name=agent_name,
                        role="Expert",
                        system_prompt="You are a helpful expert working in a team to answer multiple choice questions. You will first come up with your own answer with reasoning, present it to your team members, and then work together to reach a final solution.",
                        metadata={"backend_provider": provider, "backend_model": model_name}
                    ),
                    backend=backend
                ))
                agent_counter += 1
        
        total_agents = agent_counter
        backend_summary = build_backend_summary(config.agent_backends)
        
    elif config.backend and config.num_agents:
        # Single backend mode
        print("Running in SINGLE BACKEND mode")
        provider = config.backend.provider
        
        api_key = get_api_key(config, provider)
        
        model_name = ""
        for agent_id in range(config.num_agents):
            agent_seed = config.seed + agent_id
            backend = create_backend_from_config(
                backend_cfg=config.backend,
                api_key=api_key,
                seed=agent_seed
            )
            agent_model_name = get_model_name_from_backend(backend, provider)
            if agent_id == 0:
                model_name = agent_model_name
            
            agent_name = f"Agent-{agent_id}-{provider}-{agent_model_name}"
            
            agents.append(TeamAgent(
                profile=AgentProfile(
                    agent_id=agent_id,
                    name=agent_name,
                    role="Expert",
                    system_prompt="You are a helpful expert working in a team to answer multiple choice questions. You will first come up with your own answer with reasoning, present it to your team members, and then work together to reach a final solution.",
                    metadata={"backend_provider": provider, "backend_model": agent_model_name}
                ),
                backend=backend
            ))
        
        total_agents = config.num_agents
        if model_name:
            sanitized_model = sanitize_model_name_for_summary(model_name)
            backend_summary = f"{provider}_{sanitized_model}"
        else:
            backend_summary = provider
        
    else:
        raise ValueError("Invalid configuration: must specify backend+num_agents or agent_backends")

    # 2. Validate Fallback Model
    if config.decision_mode == "reveal_expert" and config.most_capable_model_name:
        found = False
        for agent in agents:
            if config.most_capable_model_name in agent.profile.metadata.get("backend_model", ""):
                found = True
                break
        if not found:
            print(f"WARNING: configured most_capable_model_name '{config.most_capable_model_name}' not found in any agent backend.")

    # 3. Determine Number of Problems (for run name)
    # Use limit if specified, otherwise assume full dataset (198 problems)
    num_problems = config.limit if config.limit is not None else 198
    
    # 4. Initialize W&B (will update run name after loading dataset)
    # First create a temporary run name, then update after we know the actual number of problems
    temp_run_name = config.generate_run_name(total_agents, backend_summary, num_problems)
    wandb_config = OmegaConf.to_container(cfg, resolve=True, throw_on_missing=True)
    
    run = wandb.init(
        project=config.wandb_project,
        entity=config.wandb_entity,
        name=temp_run_name,
        group=config.wandb_group,
        tags=config.wandb_tags,
        config=wandb_config
    )
    
    print(f"Experiment: {temp_run_name}")
    print(f"Dataset: {config.dataset_name}")
    print(f"Agents: {total_agents} | Rounds: {config.max_rounds}")
    
    # 5. Load Dataset
    print("Loading dataset...")
    dataset = load_dataset(config.dataset_name, split="test")
    total_problems_available = len(dataset)
    
    # Track mapping from iteration index to original problem index
    original_index_mapping = {}
    
    # Filter by question_ids from reference run if specified
    if config.reference_run_name:
        print(f"Filtering dataset using question_ids from reference run: {config.reference_run_name}")
        reference_question_ids = get_question_ids_from_run(
            config.reference_run_name,
            project=config.wandb_project,
            entity=config.wandb_entity
        )
        
        # Filter dataset to only include problems at indices matching reference question_ids
        # In GPQA Diamond, question_id is the original problem index (0-197)
        filtered_indices = [idx for idx in reference_question_ids if 0 <= idx < total_problems_available]
        dataset = dataset.select(filtered_indices)
        
        # Map iteration index to original problem index
        for iter_idx, orig_idx in enumerate(filtered_indices):
            original_index_mapping[iter_idx] = orig_idx
        
        print(f"Filtered to {len(dataset)} problems matching reference run (from {total_problems_available} total)")
        
        if len(dataset) == 0:
            raise ValueError(f"No problems found matching question_ids from reference run '{config.reference_run_name}'")
        
        if len(dataset) != len(reference_question_ids):
            print(f"WARNING: Found {len(dataset)} matching problems but reference run had {len(reference_question_ids)} question_ids")
            print("Some question_ids from reference run may be out of range for current dataset")
    
    else:
        # Assign unique problem indices (0-197) before any sampling
        # This ensures we can track which problems were evaluated even after random sampling
        print(f"Assigning problem indices 0-{total_problems_available-1} to {total_problems_available} problems")
        
        if config.limit:
            # Randomly sample problems when limit is specified
            rng = random.Random(config.seed)
            indices = list(range(total_problems_available))
            rng.shuffle(indices)
            selected_indices = sorted(indices[:config.limit])  # Sort for reproducibility
            dataset = dataset.select(selected_indices)
            # Map iteration index to original problem index
            for iter_idx, orig_idx in enumerate(selected_indices):
                original_index_mapping[iter_idx] = orig_idx
            print(f"Randomly selected {len(dataset)} problems from {total_problems_available} total")
        else:
            print(f"Running on entire dataset: {total_problems_available} problems")
            # When running full dataset, iteration index equals original index
            for i in range(total_problems_available):
                original_index_mapping[i] = i
    
    print(f"Loaded {len(dataset)} problems")
    
    # Update run name with actual number of problems
    num_problems = len(dataset)
    run_name = config.generate_run_name(total_agents, backend_summary, num_problems)
    run.name = run_name
    print(f"Updated run name: {run_name}")
    
    # 6. Execution Loop
    # Track aggregate metrics
    agent_correct_counts = {agent.profile.agent_id: 0 for agent in agents}
    team_correct_count = 0
    total_problems = 0
    run_id = run.id  # Store run ID for artifact naming
    
    for i, problem_data in enumerate(dataset):
        # Get the original problem index from the full dataset (0-197)
        # This is the unique identifier for the problem, preserved even after sampling
        original_index = original_index_mapping.get(i, i)
        
        # Use the original problem index (0-197) as unique_id and question_id
        problem_index = original_index
        question_id = problem_index
        
        print(f"\nProblem {i+1}/{len(dataset)} (question_id: {question_id})")
        
        # Use problem_index as unique_id for task
        unique_id = problem_index
        
        # Initialize Task
        # Seed should be global seed + problem index for reproducibility and uniqueness per problem
        task_seed = config.seed + i
        
        task = GPQADiamondProblemTask(
            agent_ids=[a.profile.agent_id for a in agents],
            max_rounds=config.max_rounds,
            problem_data=problem_data,
            unique_id=unique_id,
            seed=task_seed,
            decision_mode=config.decision_mode,
            most_capable_model_name=config.most_capable_model_name,
            use_llm_fallback=config.use_llm_fallback,
            llm_fallback_model=config.llm_fallback_model,
            llm_fallback_api_key=config.llm_fallback_api_key or config.openai_api_key,
        )
        
        # Execute
        result = task.execute(agents)
        
        # Update aggregate counters
        total_problems += 1
        if result.score == 1.0:  # team_score of 1.0 means correct
            team_correct_count += 1
            
        for aid, correct in result.metadata["individual_correctness"].items():
            if correct:
                agent_correct_counts[aid] += 1
        
        # Print results
        ground_truth = result.metadata["ground_truth"]
        team_answer = result.metadata["team_answer"]
        team_correct = result.score == 1.0
        
        print(f"Ground Truth: {ground_truth}")
        print(f"Team Answer: {team_answer} | Team Correct: {team_correct}")
        
        # Print individual agent performance
        for aid in sorted(result.metadata["individual_answers"].keys()):
            agent_answer = result.metadata["individual_answers"][aid]
            agent_correct = result.metadata["individual_correctness"][aid]
            agent_model = agents[aid].profile.metadata.get("backend_model", "Unknown")
            print(f"  Agent {aid} ({agent_model}): {agent_answer} | Correct: {agent_correct}")
        
        # Log per-problem data to W&B history
        log_data: Dict[str, Any] = {
            "question_id": str(question_id),  # Use question_id to identify the specific question in the dataset (critical for random sampling)
            "problem_index": i,  # Index in the current run (may differ if subset was sampled)
            "ground_truth": ground_truth,
            "team_answer": team_answer,
            "team_score": result.score,
        }
        
        # Log individual agent data
        for aid in sorted(result.metadata["individual_answers"].keys()):
            log_data[f"agent_{aid}_answer"] = result.metadata["individual_answers"][aid]
            log_data[f"agent_{aid}_correctness"] = 1.0 if result.metadata["individual_correctness"][aid] else 0.0
            # Commented out to reduce W&B payload size
            # log_data[f"agent_{aid}_solution"] = result.metadata["individual_solutions"][aid]
        
        # Log decision mode metadata
        if result.metadata.get("declared_best_agent_id") is not None:
            log_data["declared_best_agent_id"] = result.metadata["declared_best_agent_id"]
        if result.metadata.get("coordinator_agent_id") is not None:
            log_data["coordinator_agent_id"] = result.metadata["coordinator_agent_id"]
        if result.metadata.get("revealed_expert_agent_id") is not None:
            log_data["revealed_expert_agent_id"] = result.metadata["revealed_expert_agent_id"]
        
        # Commented out to reduce W&B payload size
        # log_data["team_solution"] = result.metadata["team_solution"]
        
        wandb.log(log_data, step=i)
        
        # Log trajectories as W&B artifacts
        artifact_name = f"trajectories-problem-{i}-{unique_id}-{run_id}"
        artifact = wandb.Artifact(artifact_name, type="trajectories")
        
        for agent in agents:
            agent_id = agent.profile.agent_id
            trajectory_text = agent.backend.format_full_prompt(
                agent_profile=agent.profile,
                trajectory=agent.trajectory
            )
            
            filename = f"problem_{i}_{unique_id}_agent_{agent_id}_trajectory.txt"
            with artifact.new_file(filename, mode="w") as f:
                f.write(trajectory_text)
        
        run.log_artifact(artifact)
        
        # Clear agent trajectories for next problem
        for agent in agents:
            agent.trajectory.clear()
    
    # 7. Compute Aggregate Metrics
    team_accuracy = team_correct_count / total_problems if total_problems > 0 else 0.0
    
    individual_accuracies = {
        aid: count / total_problems if total_problems > 0 else 0.0
        for aid, count in agent_correct_counts.items()
    }
    
    avg_individual_accuracy = statistics.mean(individual_accuracies.values()) if individual_accuracies else 0.0
    best_individual_accuracy = max(individual_accuracies.values()) if individual_accuracies else 0.0
    
    # Teamwork scores (improvement over baselines)
    teamwork_vs_avg = team_accuracy - avg_individual_accuracy
    teamwork_vs_best = team_accuracy - best_individual_accuracy
    
    # Log aggregate metrics to W&B summary
    wandb.run.summary["team_accuracy"] = team_accuracy
    wandb.run.summary["avg_individual_accuracy"] = avg_individual_accuracy
    wandb.run.summary["best_individual_accuracy"] = best_individual_accuracy
    wandb.run.summary["teamwork_vs_avg_improvement"] = teamwork_vs_avg
    wandb.run.summary["teamwork_vs_best_improvement"] = teamwork_vs_best
    
    # Log individual model accuracies
    for aid, accuracy in individual_accuracies.items():
        agent_model = agents[aid].profile.metadata.get("backend_model", f"Agent_{aid}")
        wandb.run.summary[f"agent_{aid}_accuracy"] = accuracy
        wandb.run.summary[f"agent_{aid}_model"] = agent_model
    
    # Remove per-problem metrics from summary to avoid clutter
    # (they're already in history)
    metrics_to_remove = [
        "question_id", "problem_index", "ground_truth", "team_answer", "team_score",
        "agent_0_answer", "agent_1_answer", "agent_2_answer", "agent_3_answer",
        "agent_0_correctness", "agent_1_correctness", "agent_2_correctness", "agent_3_correctness",
    ]
    for metric in metrics_to_remove:
        if wandb.run.summary.get(metric) is not None:
            try:
                del wandb.run.summary[metric]
            except Exception:
                pass
    
    # Print summary
    print("\n" + "="*80)
    print("EXPERIMENT SUMMARY")
    print("="*80)
    print(f"Total Problems: {total_problems}")
    print(f"Team Accuracy: {team_accuracy:.4f}")
    print(f"Average Individual Accuracy: {avg_individual_accuracy:.4f}")
    print(f"Best Individual Accuracy: {best_individual_accuracy:.4f}")
    print(f"Teamwork vs Average Improvement: {teamwork_vs_avg:+.4f}")
    print(f"Teamwork vs Best Improvement: {teamwork_vs_best:+.4f}")
    print("\nIndividual Model Accuracies:")
    for aid in sorted(individual_accuracies.keys()):
        agent_model = agents[aid].profile.metadata.get("backend_model", f"Agent_{aid}")
        print(f"  Agent {aid} ({agent_model}): {individual_accuracies[aid]:.4f}")
    print("="*80)
    
    wandb.finish()


if __name__ == "__main__":
    main()


