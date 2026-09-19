import numpy as np
from typing import Dict, Any, List, Optional

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    F = None
    TORCH_AVAILABLE = False
    nn = object


LOGIC_GATES = {
    'AND': lambda a, b: a & b,
    'OR': lambda a, b: a | b,
    'XOR': lambda a, b: a ^ b,
    'NAND': lambda a, b: ~(a & b),
    'NOR': lambda a, b: ~(a | b),
    'XNOR': lambda a, b: ~(a ^ b),
}


class DiffLogicBFEncoder(nn.Module if TORCH_AVAILABLE else object):
    def __init__(self, tape_length: int = 48, hidden_size: int = 64, device: str = 'cpu'):
        if not TORCH_AVAILABLE:
            raise RuntimeError(
                "PyTorch required for the DiffLogic DEMIURGE layer; "
                "install with: pip install primordium[neural]"
            )
        super().__init__()
        self.tape_length = tape_length
        self.hidden_size = hidden_size
        self.device = device

        self.gate_logits = nn.Parameter(torch.zeros(tape_length, 16, device=device))
        nn.init.xavier_uniform_(self.gate_logits)

        self.perception = nn.Linear(tape_length, hidden_size, device=device)
        self.update = nn.Linear(hidden_size, tape_length, device=device)

    def get_gate_probs(self) -> torch.Tensor:
        return F.softmax(self.gate_logits, dim=-1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        gate_probs = self.get_gate_probs()
        gate_weighted = (gate_probs * 16).sum(dim=-1)
        logic_output = x * gate_weighted.unsqueeze(0)
        perceived = self.perception(logic_output)
        return F.relu(perceived)

    def encode_tape(self, tape: np.ndarray) -> torch.Tensor:
        if len(tape) != self.tape_length:
            tape = np.pad(tape, (0, self.tape_length - len(tape)))[:self.tape_length]
        normalized = torch.from_numpy(tape.astype(np.float32) / 255.0).to(self.device)
        with torch.no_grad():
            self.gate_logits.data = normalized.unsqueeze(1).expand(-1, 16) * 2 - 1
        return self.perception.weight


class DiffLogicNeuralEvaluator:
    def __init__(self, tape_length: int = 48, hidden_size: int = 64, device: str = 'cpu'):
        self.tape_length = tape_length
        self.hidden_size = hidden_size
        self.device = device
        self.encoder = DiffLogicBFEncoder(tape_length, hidden_size, device)

    def evaluate_on_copy_task(self, tape: np.ndarray) -> float:
        copy_count = np.sum(tape == 46)
        loop_start = np.sum(tape == 91)
        loop_end = np.sum(tape == 93)
        loop_balance = 1.0 - abs(loop_start - loop_end) / max(loop_start + loop_end, 1)
        right_moves = np.sum(tape == 62)
        left_moves = np.sum(tape == 60)
        movement = (right_moves + left_moves) / max(len(tape), 1)

        fitness = 0.3 * min(copy_count / 5, 1.0) + 0.3 * loop_balance + 0.4 * movement
        return fitness

    def evaluate_task(self, tape: np.ndarray, task_inputs: List[np.ndarray],
                      task_outputs: List[np.ndarray]) -> float:
        self.encoder.encode_tape(tape)
        total_loss = 0.0

        for inp, expected in zip(task_inputs, task_outputs):
            inp_tensor = torch.from_numpy(inp.astype(np.float32)).unsqueeze(0).to(self.device)
            expected_tensor = torch.from_numpy(expected.astype(np.float32)).unsqueeze(0).to(self.device)

            with torch.no_grad():
                output = self.encoder(inp_tensor)
                loss = F.mse_loss(output.mean(), expected_tensor.mean())
                total_loss += loss.item()

        avg_loss = total_loss / len(task_inputs) if task_inputs else 1.0
        return 1.0 / (1.0 + avg_loss)


class DiffLogicDemiurgeLayer:
    def __init__(self, config: Dict[str, Any]):
        self.enabled = config.get('enabled', True)
        self.tape_length = config.get('tape_length', 48)
        self.hidden_size = config.get('hidden_size', 64)
        self.device = config.get('device', 'cpu')
        if self.device == 'auto':
            self.device = 'mps' if torch.backends.mps.is_available() else 'cpu'

        if self.enabled:
            try:
                self.evaluator = DiffLogicNeuralEvaluator(
                    self.tape_length, self.hidden_size, self.device
                )
            except Exception as e:
                print(f"Warning: Failed to initialize DiffLogic DEMIURGE: {e}")
                self.evaluator = None
        else:
            self.evaluator = None

    def evaluate_scroll(self, tape: np.ndarray,
                        task_inputs: Optional[List[np.ndarray]] = None,
                        task_outputs: Optional[List[np.ndarray]] = None) -> float:
        if not self.enabled or self.evaluator is None:
            return 0.0

        fitness = 0.0
        weights = []

        copy_fitness = self.evaluator.evaluate_on_copy_task(tape)
        fitness += copy_fitness
        weights.append(1.0)

        if task_inputs and task_outputs:
            task_fitness = self.evaluator.evaluate_task(tape, task_inputs, task_outputs)
            fitness += task_fitness
            weights.append(1.0)

        return fitness / len(weights) if weights else 0.0

    def after_interaction(self, soup, i: int, j: int, steps: int) -> None:
        if not self.enabled or self.evaluator is None:
            return

        scroll_i = soup.scrolls[i]
        scroll_j = soup.scrolls[j]
        scroll_i.fitness = self.evaluate_scroll(scroll_i.tape)
        scroll_j.fitness = self.evaluate_scroll(scroll_j.tape)

    def after_epoch(self, soup, epoch: int) -> Dict[str, Any]:
        if not self.enabled or not soup.scrolls:
            return {}

        fitnesses = [s.fitness for s in soup.scrolls]
        return {
            'fitness_mean': np.mean(fitnesses),
            'fitness_std': np.std(fitnesses),
            'fitness_max': np.max(fitnesses),
            'fitness_min': np.min(fitnesses),
        }


def create_difflogic_demiurge(config: Dict[str, Any]) -> DiffLogicDemiurgeLayer:
    return DiffLogicDemiurgeLayer(config)
