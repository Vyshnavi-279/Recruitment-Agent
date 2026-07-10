"""Audit log for recording agent trajectory steps."""

import json
import os
from datetime import datetime

from src.schemas import TrajectoryStep


class AuditLog:
    """Records and persists the agent's trajectory as a JSON audit trail."""

    def __init__(self) -> None:
        self._steps: list[TrajectoryStep] = []

    def append(self, step: TrajectoryStep) -> None:
        """Append a single trajectory step to the in-memory log.

        Args:
            step: The TrajectoryStep to record.
        """
        self._steps.append(step)

    def save(self, path: str | None = None) -> str:
        """Write the full trajectory as JSON to disk.

        Args:
            path: Optional file path. If None, defaults to
                  logs/trajectories/{timestamp}.json.

        Returns:
            The path to which the file was written.
        """
        if path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_dir = os.path.join("logs", "trajectories")
            os.makedirs(log_dir, exist_ok=True)
            path = os.path.join(log_dir, f"{timestamp}.json")

        data = [step.model_dump() for step in self._steps]

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        return path