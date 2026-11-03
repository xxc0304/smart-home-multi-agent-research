# Teamwork

A harness for multi-agent LLM teamwork experiments.

This is the official codebase for **"Multi-Agent Teams Hold Experts Back"**. We find that LLM teams systematically fail to leverage expertise, underperforming their best member by 6-41% even when explicitly told who the expert is. This toolkit enables replication of our experiments and extension to new tasks and models.

**Paper:** [Multi-Agent Teams Hold Experts Back](https://arxiv.org/abs/2602.01011)

## Overview

This toolkit enables experimentation with collaborative AI teams:
- Run built-in ranking and problem-solving tasks with configurable agent teams
- Test homogeneous and heterogeneous team compositions
- Experiment with information distribution strategies (none, full, distributed)
- Add custom tasks and model backends

## Project Structure

```
teamwork/
├── teamwork/                   # Core package
│   ├── tasks/                  # Task implementations
│   │   ├── task.py             # Abstract base class
│   │   ├── collaborative_ranking_task.py
│   │   ├── collaborative_multiple_choice_task.py
│   │   ├── collaborative_short_answer_task.py
│   │   ├── lost_at_sea_task.py          # Example ranking task
│   │   ├── gpqa_diamond_problem_task.py # Example MC task
│   │   └── simpleqa_problem_task.py     # Example short answer task
│   ├── backends.py             # LLM provider backends (OpenAI, Anthropic, etc.)
│   ├── agent.py                # TeamAgent implementation
│   ├── profiles.py             # AgentProfile data structures
│   └── conversation.py         # Conversation/trajectory handling
├── experiments/                # Experiment runners
│   ├── configs/                # Hydra configuration files
│   ├── run_lost_at_sea.py      # Ranking task runner
│   ├── run_gpqa_diamond.py     # MC task runner
│   └── ...
└── tests/                      # Test suite
```

## Getting Started

### Setup

1. Create and activate a virtual environment (Python 3.9+):
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install the package and dependencies:
```bash
pip install -e .
pip install -e ".[dev]"  # Optional: includes pytest, ruff, pyright
```

3. Configure API keys by copying `.env.example` to `.env` and adding your keys:
```bash
cp .env.example .env
```

The harness supports multiple LLM providers. Add the keys for providers you plan to use:

```bash
OPENAI_API_KEY=...       # OpenAI models (gpt-4o, gpt-4o-mini)
ANTHROPIC_API_KEY=...    # Anthropic models (claude-3-5-haiku, claude-3-5-sonnet)
OPENROUTER_API_KEY=...   # Gemini models via OpenRouter
WANDB_API_KEY=...        # Weights & Biases for experiment logging (optional)
```

**Important:** Never commit your `.env` file - it's already in `.gitignore`


## Running Experiments

Experiments use [Hydra](https://hydra.cc/) for configuration. Override any parameter via command line. Results are logged to [Weights & Biases](https://wandb.ai/) (requires `WANDB_API_KEY` in `.env`). See all available options in `experiments/configs/`.

### Collaborative Ranking Tasks

Teams rank items against expert ground truth. Scored by L1 distance (lower is better).

```bash
# Lost at Sea - rank 15 survival items
python experiments/run_lost_at_sea.py

# NASA Moon Survival - rank 15 items for lunar trek
python experiments/run_moon_survival.py

# Student Body President - rank 4 candidates
python experiments/run_student_body_president.py
```

### Problem-Solving Tasks

Teams solve problems collaboratively. Scored by accuracy (higher is better).

```bash
# MATH-500 - mathematical problem solving
python experiments/run_math_500.py

# GPQA Diamond - graduate-level science questions
python experiments/run_gpqa_diamond.py

# SimpleQA - short-answer questions
python experiments/run_simpleqa.py

# MMLU Pro - multiple choice across domains
python experiments/run_mmlu_pro.py

# HLE (Humanity's Last Exam) - text-only questions
python experiments/run_hle_text_only.py
```

### Key Configuration Options

```bash
# Team composition
python experiments/run_lost_at_sea.py num_agents=4 max_rounds=3 seed=42

# Information distribution modes
python experiments/run_lost_at_sea.py expert_info_mode=distributed  # none, full, single_expert, distributed

# Decision modes
python experiments/run_lost_at_sea.py decision_mode=reveal_expert  # expert_not_mentioned, reveal_expert, etc.

# Brainstorming modes (ranking tasks only)
python experiments/run_lost_at_sea.py interactive_brainstorming_mode=true  # true=one-stage, false=two-stage

# Single backend (homogeneous team)
python experiments/run_lost_at_sea.py backend.provider=anthropic backend.model=claude-3-5-haiku-20241022

# Multiple backends (heterogeneous team)
python experiments/run_lost_at_sea.py \
    'agent_backends=[{provider: openai, count: 2, model: gpt-4o}, {provider: anthropic, count: 2}]'
```


## Implementing New Tasks

Extend one of three base classes depending on your task type.

### Abstract Base Class

All tasks inherit from `Task` in `teamwork/tasks/task.py`:

```python
class Task(abc.ABC):
    def get_task_description(self, agent_id: int) -> str:
        """Task prompt for an agent (can be personalized per agent)."""

    def score_solution(self, solution: str) -> float:
        """Evaluate solution, return numeric score."""

    def get_hidden_info(self, agent_id: int) -> str:
        """Agent-specific hidden information."""

    def execute(self, agents: List[TeamAgent]) -> TaskResult:
        """Orchestrate full task: individual phase, collaboration, final answer."""
```

### Ranking Tasks

Extend `CollaborativeRankingTask` from `teamwork/tasks/collaborative_ranking_task.py`.

**Properties to define:**
- `items: List[str]` - items to rank
- `specialized_information: List[str]` - expert info per item
- `ground_truth_ranking: List[int]` - correct ranking (1-indexed)

**Methods to implement:**
- `get_task_description(agent_id)` - scenario description
- `_parse_ranking(text) -> Dict[str, int]` - extract ranking from response

**Scoring:** L1 distance from ground truth (lower = better)

**Example:** `teamwork/tasks/lost_at_sea_task.py`

### Multiple Choice Tasks

Extend `CollaborativeMultipleChoiceQuestionTask` from `teamwork/tasks/collaborative_multiple_choice_task.py`.

**Methods to implement:**
- `get_task_description(agent_id)` - question with formatted options
- `get_ground_truth() -> str` - correct answer letter (A-J)

**Scoring:** 1.0 for correct, 0.0 for incorrect

**Example:** `teamwork/tasks/gpqa_diamond_problem_task.py`

### Short Answer Tasks

Extend `CollaborativeShortAnswerTask` from `teamwork/tasks/collaborative_short_answer_task.py`.

**Methods to implement:**
- `get_task_description(agent_id)` - question prompt
- `get_ground_truth() -> str` - canonical answer

**Scoring:** Uses LLM autorating to check answer equivalence

**Example:** `teamwork/tasks/simpleqa_problem_task.py`


## Adding New Model Backends

Backends live in `teamwork/backends.py`. Inherit from `LLMBackend` and implement `invoke()`.

### Required Interface

```python
class LLMBackend(abc.ABC):
    @abstractmethod
    def invoke(
        self,
        *,
        agent_profile: AgentProfile,
        trajectory: Trajectory,
    ) -> str:
        """Perform inference and return model response."""
```

**Input data structures:**
- `AgentProfile`: `agent_id`, `name`, `role`, `system_prompt`, `persona`, `hidden_context`
- `Trajectory`: list of `Turn` objects (`speaker_id`, `content`)

**Inherited utilities:**
- `self._build_system_message(agent_profile)` - construct system message from profile
- `self.usage_stats.add_call(input_tokens, output_tokens)` - track token usage

### Steps to Add a Backend

1. **Create class** inheriting from `LLMBackend` in `teamwork/backends.py`
2. **Implement `invoke()`** - build messages, call API, track tokens, return response
3. **Add to factory** - add provider case in `create_backend()` function
4. **Add API key handling** - update `get_api_key()` in `teamwork/backend_utils.py`

**Reference implementations:** `OpenAIBackend`, `AnthropicBackend`, `OpenRouterBackend`


## Development

### Architecture Overview

1. Instantiate `AgentProfile` objects for each participant with role, system prompt, persona, and optional hidden context.
2. Provide an `LLMBackend` implementation that knows how to call your inference APIs.
3. Create `TeamAgent` instances and define a `Task` for them to complete.
4. Call `task.execute(agents)` to run the task with independent and collaborative phases.

### Makefile Targets

```bash
make check    # Run all checks (tests + linting + typing)
make test     # Run pytest
make lint     # Run ruff check + pyright
make format   # Run ruff format
```


## Citation

If you use this codebase in your research, please cite our paper:

```bibtex
@article{pappu2026multiagent,
  title={Multi-Agent Teams Hold Experts Back},
  author={Pappu, Aneesh and El, Batu and Cao, Hancheng and di Nolfo, Carmelo and Sun, Yanchao and Cao, Meng and Zou, James},
  journal={arXiv preprint arXiv:2602.01011},
  year={2026}
}
```


## License

This project is licensed under the MIT License - see below for details.

```
MIT License

Copyright (c) 2026 Aneesh Pappu, Batu El, Hancheng Cao, Carmelo di Nolfo, Yanchao Sun, Meng Cao, James Zou

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

