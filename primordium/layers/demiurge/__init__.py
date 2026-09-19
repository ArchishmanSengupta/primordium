"""DEMIURGE: Neural encoding layer.

This layer transforms BrainFuck programs into neural network weights and
evaluates their fitness on computational tasks.

The key insight is that BF instructions can be interpreted as neural network
operations - the tape is the "memory", pointer movements are "routing",
and increment/decrement are "weight updates".
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    nn = object


# BF instruction to neural operation mapping
class BFEncoder(nn.Module if TORCH_AVAILABLE else object):
    """Encode BF tape as neural network weights."""

    def __init__(self, tape_length: int, hidden_size: int = 64):
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch required for DEMIURGE")

        super().__init__()
        self.tape_length = tape_length
        self.hidden_size = hidden_size

        # Map each tape cell to a weight
        # Each cell can hold 0-255, which maps to [-1, 1] weight range
        self.tape_weights = nn.Parameter(
            torch.randn(tape_length, hidden_size) * 0.1
        )

        # Instruction pointer routing
        self.ip_router = nn.Linear(hidden_size, tape_length)

        # Data pointer routing
        self.dp_router = nn.Linear(hidden_size, tape_length)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Process input through BF-encoded network.

        Args:
            x: Input tensor

        Returns:
            Output tensor
        """
        # Use tape weights to transform input
        # Each input element selects a weight row
        x.shape[0]

        # Normalize input to index tape positions
        indices = (x.abs().mean(dim=-1) * self.tape_length).long()
        indices = indices.clamp(0, self.tape_length - 1)

        # Gather weights
        selected_weights = self.tape_weights[indices]  # [batch, hidden]

        # Apply transformation
        output = selected_weights.mean(dim=1)  # [batch]

        return output


class NeuralEvaluator:
    """Evaluate BF programs using neural encoding."""

    def __init__(
        self,
        tape_length: int = 48,
        hidden_size: int = 64,
        device: str = 'cpu'
    ):
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch required for DEMIURGE")

        self.tape_length = tape_length
        self.hidden_size = hidden_size
        self.device = device

        self.encoder = BFEncoder(tape_length, hidden_size).to(device)

    def encode_tape(self, tape: np.ndarray) -> torch.Tensor:
        """Convert BF tape to neural weights.

        Args:
            tape: Byte array from scroll

        Returns:
            Torch tensor of weights
        """
        if len(tape) != self.tape_length:
            tape = np.pad(tape, (0, self.tape_length - len(tape)))[:self.tape_length]

        # Normalize to [0, 1]
        normalized = tape.astype(np.float32) / 255.0

        # Set encoder weights
        with torch.no_grad():
            weights = torch.from_numpy(normalized).unsqueeze(1).expand(
                self.tape_length, self.hidden_size
            )
            self.encoder.tape_weights.data = weights * 2 - 1

        return self.encoder.tape_weights.data

    def evaluate_task(
        self,
        tape: np.ndarray,
        task_inputs: List[np.ndarray],
        task_outputs: List[np.ndarray],
    ) -> float:
        """Evaluate a scroll on a task.

        Args:
            tape: BF tape to evaluate
            task_inputs: List of input arrays
            task_outputs: Expected output arrays

        Returns:
            Fitness score [0, 1]
        """
        if not TORCH_AVAILABLE:
            return 0.0

        self.encode_tape(tape)

        total_loss = 0.0

        for inp, expected in zip(task_inputs, task_outputs):
            inp_tensor = torch.from_numpy(inp.astype(np.float32)).unsqueeze(0).to(self.device)
            expected_tensor = torch.from_numpy(expected.astype(np.float32)).unsqueeze(0).to(self.device)

            with torch.no_grad():
                output = self.encoder(inp_tensor)
                loss = nn.MSELoss()(output, expected_tensor.mean())
                total_loss += loss.item()

        avg_loss = total_loss / len(task_inputs) if task_inputs else 1.0
        fitness = 1.0 / (1.0 + avg_loss)

        return fitness

    def evaluate_on_copy_task(self, tape: np.ndarray) -> float:
        """Evaluate copy task - can the program copy data?

        This is a fundamental task: can the program read from one
        location and write to another?

        Args:
            tape: BF tape to evaluate

        Returns:
            Fitness score
        """
        if not TORCH_AVAILABLE:
            return 0.0

        # Simple test: does the tape have copy instructions?
        copy_count = np.sum(tape == 46)  # '.' = copy

        # Loop count (ability to repeat operations)
        loop_start = np.sum(tape == 91)  # '['
        loop_end = np.sum(tape == 93)    # ']'

        # Balance of loops
        loop_balance = 1.0 - abs(loop_start - loop_end) / max(loop_start + loop_end, 1)

        # Movement capability (can move around tape)
        right_moves = np.sum(tape == 62)  # '>'
        left_moves = np.sum(tape == 60)   # '<'

        movement = (right_moves + left_moves) / max(len(tape), 1)

        # Compute fitness
        fitness = (
            0.3 * min(copy_count / 5, 1.0) +
            0.3 * loop_balance +
            0.4 * movement
        )

        return fitness


class DemiurgeLayer:
    """DEMIURGE neural encoding layer.

    Transforms BF programs to neural networks and evaluates fitness.
    """

    def __init__(self, config: Dict[str, Any]):
        self.enabled = config.get('enabled', True)

        # Neural encoding settings
        self.tape_length = config.get('tape_length', 48)
        self.hidden_size = config.get('hidden_size', 64)

        # Device for neural computation
        self.device = config.get('device', 'cpu')

        # Task settings
        self.eval_copy_task = config.get('eval_copy_task', True)
        self.eval_custom_tasks = config.get('eval_custom_tasks', [])

        # Initialize evaluator if PyTorch available
        if TORCH_AVAILABLE and self.enabled:
            try:
                self.evaluator = NeuralEvaluator(
                    tape_length=self.tape_length,
                    hidden_size=self.hidden_size,
                    device=self.device
                )
            except Exception as e:
                print(f"Warning: Failed to initialize DEMIURGE: {e}")
                self.evaluator = None
        else:
            self.evaluator = None

    def evaluate_scroll(
        self,
        tape: np.ndarray,
        task_inputs: Optional[List[np.ndarray]] = None,
        task_outputs: Optional[List[np.ndarray]] = None,
    ) -> float:
        """Evaluate fitness of a scroll.

        Args:
            tape: BF tape to evaluate
            task_inputs: Optional custom task inputs
            task_outputs: Optional custom task expected outputs

        Returns:
            Fitness score [0, 1]
        """
        if not self.enabled or self.evaluator is None:
            return 0.0

        fitness = 0.0
        weights = []

        # Evaluate copy task
        if self.eval_copy_task:
            copy_fitness = self.evaluator.evaluate_on_copy_task(tape)
            fitness += copy_fitness
            weights.append(1.0)

        # Evaluate custom tasks
        if task_inputs and task_outputs:
            for inp, out in zip(task_inputs, task_outputs):
                task_fitness = self.evaluator.evaluate_task(tape, [inp], [out])
                fitness += task_fitness
                weights.append(1.0)

        # Normalize
        if weights:
            fitness /= len(weights)

        return fitness

    def after_interaction(self, soup, i: int, j: int, steps: int) -> None:
        """After interaction, evaluate fitness of modified scrolls.

        Args:
            soup: The soup
            i: First scroll index
            j: Second scroll index
            steps: Number of steps executed
        """
        if not self.enabled or self.evaluator is None:
            return

        # Evaluate fitness for modified scrolls
        scroll_i = soup.scrolls[i]
        scroll_j = soup.scrolls[j]

        scroll_i.fitness = self.evaluate_scroll(scroll_i.tape)
        scroll_j.fitness = self.evaluate_scroll(scroll_j.tape)

    def after_epoch(self, soup, epoch: int) -> Dict[str, Any]:
        """After epoch, return fitness statistics.

        Args:
            soup: The soup
            epoch: Current epoch number

        Returns:
            Dictionary of statistics
        """
        if not self.enabled or not soup.scrolls:
            return {}

        # Compute fitness statistics
        fitnesses = [s.fitness for s in soup.scrolls]

        stats = {
            'fitness_mean': np.mean(fitnesses),
            'fitness_std': np.std(fitnesses),
            'fitness_max': np.max(fitnesses),
            'fitness_min': np.min(fitnesses),
        }

        return stats


def create_demiurge(config: Dict[str, Any]) -> DemiurgeLayer:
    """Factory function to create DEMIURGE layer.

    Args:
        config: Configuration dictionary

    Returns:
        DemiurgeLayer instance
    """
    return DemiurgeLayer(config)
