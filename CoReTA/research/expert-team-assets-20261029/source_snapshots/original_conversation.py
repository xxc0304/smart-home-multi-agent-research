"""Conversation abstractions for multi-LLM teamwork experiments."""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class Turn:
    """A single entry in the shared conversation trajectory."""

    speaker_id: int
    content: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "speaker_id": self.speaker_id,
            "content": self.content,
        }


@dataclass
class Trajectory:
    """Shared conversation trajectory accessible to all agents."""

    turns: List[Turn] = field(default_factory=list)

    def append(self, turn: Turn) -> None:
        self.turns.append(turn)

    def extend(self, turns: Iterable[Turn]) -> None:
        self.turns.extend(turns)

    def last_turn(self) -> Optional[Turn]:
        if not self.turns:
            return None
        return self.turns[-1]

    def as_dict(self) -> Dict[str, Any]:
        return {"turns": [turn.as_dict() for turn in self.turns]}

    def clear(self) -> None:
        """Clear all turns from the trajectory."""
        self.turns.clear()

    def clone(self) -> "Trajectory":
        """Create a deep copy of the trajectory and its turns."""

        copies = [Turn(speaker_id=turn.speaker_id, content=turn.content) for turn in self.turns]
        return Trajectory(turns=copies)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Trajectory":
        """Create a Trajectory object from a dictionary representation.

        Expected dictionary structure:
        {
            "turns": [
                {"speaker_id": 1, "content": "Hello everyone"},
                {"speaker_id": 2, "content": "Hi there!"},
                {"speaker_id": -1, "content": "System message"}
            ]
        }

        The "turns" key is optional and defaults to an empty list if missing.
        """

        turns = []
        for turn_dict in data.get("turns", []):
            turn = Turn(speaker_id=turn_dict["speaker_id"], content=turn_dict["content"])
            turns.append(turn)
        return cls(turns=turns)


def format_turn_content(turn: Turn, viewer_agent_id: int) -> str:
    """Format turn content as it appears to a specific agent.

    When an agent views a trajectory, messages are formatted with speaker prefixes
    to distinguish who said what. This function replicates the exact formatting
    that backends apply when building prompts for LLM APIs.

    Args:
        turn: The turn to format
        viewer_agent_id: The agent ID viewing this turn

    Returns:
        Formatted content with appropriate speaker prefix:
        - If viewer is the speaker: raw content (no prefix)
        - If speaker is System (ID -1): "System: {content}"
        - Otherwise: "Agent {speaker_id}: {content}"
    """
    if turn.speaker_id == viewer_agent_id:
        return turn.content
    else:
        speaker = "System" if turn.speaker_id == -1 else f"Agent {turn.speaker_id}"
        return f"{speaker}: {turn.content}"

