"""PROMETHEUS: Technology layer.

Adds tool use, external memory, and prediction capabilities.
Named after the Titan who brought fire/technology to humanity.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
from collections import deque


class ToolRegistry:
    """Registry of available tools that scrolls can use."""

    def __init__(self):
        self.tools = {}

    def register_tool(self, name: str, tool: Any):
        """Register a tool.

        Args:
            name: Tool name
            tool: Tool function/object
        """
        self.tools[name] = tool

    def get_tool(self, name: str) -> Optional[Any]:
        """Get a tool by name."""
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        """List all available tools."""
        return list(self.tools.keys())


class ExternalMemory:
    """External shared memory that scrolls can read/write."""

    def __init__(self, size: int = 256):
        self.size = size
        self.memory = np.zeros(size, dtype=np.uint8)
        self.write_history = deque(maxlen=1000)

    def read(self, address: int, length: int = 1) -> np.ndarray:
        """Read from memory.

        Args:
            address: Start address
            length: Number of bytes to read

        Returns:
            Array of bytes
        """
        address = address % self.size
        if length == 1:
            return self.memory[address:address+1]
        end = (address + length) % self.size
        if end > address:
            return self.memory[address:end]
        else:
            return np.concatenate([self.memory[address:], self.memory[:end]])

    def write(self, address: int, data: np.ndarray):
        """Write to memory.

        Args:
            address: Start address
            data: Data to write
        """
        address = address % self.size
        length = len(data)
        end = (address + length) % self.size

        if end > address:
            self.memory[address:end] = data[:end - address]
        else:
            self.memory[address:] = data[:self.size - address]
            self.memory[:end] = data[self.size - address:]

        self.write_history.append({
            'address': address,
            'data': data.copy(),
        })

    def get_statistics(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            'unique_values': len(np.unique(self.memory)),
            'entropy': self._compute_entropy(),
            'write_count': len(self.write_history),
        }

    def _compute_entropy(self) -> float:
        """Compute entropy of memory contents."""
        values, counts = np.unique(self.memory, return_counts=True)
        probs = counts / self.size
        entropy = -np.sum(probs * np.log2(probs + 1e-10))
        return entropy


class PredictionModel:
    """Simple prediction model for outcome forecasting."""

    def __init__(self, history_size: int = 1000):
        self.history_size = history_size
        self.step_history = deque(maxlen=history_size)

    def record(self, steps: int):
        """Record a step count."""
        self.step_history.append(steps)

    def predict_outcome(self) -> Dict[str, float]:
        """Predict likely outcomes based on history."""
        if not self.step_history:
            return {'mean': 0, 'std': 0, 'min': 0, 'max': 0}

        history = np.array(self.step_history)
        return {
            'mean': float(np.mean(history)),
            'std': float(np.std(history)),
            'min': float(np.min(history)),
            'max': float(np.max(history)),
        }


class PrometheusLayer:
    """PROMETHEUS layer for tool use and external memory.

    Adds:
    - External shared memory
    - Tool registry
    - Prediction capabilities
    - Environment interaction
    """

    def __init__(self, config: Dict[str, Any]):
        self.enabled = config.get('enabled', True)

        # External memory settings
        self.external_memory_size = config.get('external_memory_size', 256)

        # Prediction settings
        self.prediction_enabled = config.get('prediction_enabled', True)
        self.prediction_history_size = config.get('prediction_history_size', 1000)

        # Initialize components
        self.tool_registry = ToolRegistry()
        self.external_memory = ExternalMemory(self.external_memory_size)
        self.prediction_model = PredictionModel(self.prediction_history_size)

        # Register default tools
        self._register_default_tools()

    def _register_default_tools(self):
        """Register default tools."""

        # Tool: Read from external memory
        def read_memory(address: int, length: int = 1):
            return self.external_memory.read(address, length)

        # Tool: Write to external memory
        def write_memory(address: int, data: List[int]):
            self.external_memory.write(address, np.array(data, dtype=np.uint8))

        # Tool: Get memory stats
        def get_memory_stats():
            return self.external_memory.get_statistics()

        self.tool_registry.register_tool('read', read_memory)
        self.tool_registry.register_tool('write', write_memory)
        self.tool_registry.register_tool('memory_stats', get_memory_stats)

    def before_interaction(self, soup, i: int, j: int) -> None:
        """Before interaction, potentially use tools."""
        if not self.enabled:
            return

        # Could check for tool-use patterns in scrolls
        # For now, just track that interaction will happen
        pass

    def after_interaction(self, soup, i: int, j: int, steps: int) -> None:
        """After interaction, record outcomes and use external memory."""
        if not self.enabled:
            return

        # Record steps for prediction
        if self.prediction_enabled:
            self.prediction_model.record(steps)

        # Periodically write to external memory
        # Use high-fitness scrolls as "insights"
        if hasattr(soup.scrolls[i], 'fitness') and soup.scrolls[i].fitness > 0.5:
            # Write first few bytes of high-fitness scroll to memory
            address = i * 8  # Simple addressing scheme
            self.external_memory.write(
                address,
                soup.scrolls[i].tape[:8]
            )

    def after_epoch(self, soup, epoch: int) -> Dict[str, Any]:
        """After epoch, return statistics."""
        if not self.enabled:
            return {}

        stats = {
            'prometheus_tools': len(self.tool_registry.list_tools()),
        }

        # Memory statistics
        mem_stats = self.external_memory.get_statistics()
        stats.update({
            f'prometheus_{k}': v for k, v in mem_stats.items()
        })

        # Prediction statistics
        if self.prediction_enabled:
            pred = self.prediction_model.predict_outcome()
            stats['prometheus_pred_mean'] = pred['mean']

        return stats

    def use_tool(self, tool_name: str, *args, **kwargs) -> Any:
        """Use a tool from the registry."""
        tool = self.tool_registry.get_tool(tool_name)
        if tool is None:
            raise ValueError(f"Tool not found: {tool_name}")
        return tool(*args, **kwargs)

    def read_external_memory(self, address: int, length: int = 1) -> np.ndarray:
        """Read from external memory."""
        return self.external_memory.read(address, length)

    def write_external_memory(self, address: int, data: List[int]):
        """Write to external memory."""
        self.external_memory.write(address, np.array(data, dtype=np.uint8))


def create_prometheus(config: Dict[str, Any]) -> PrometheusLayer:
    """Factory function to create PROMETHEUS layer."""
    return PrometheusLayer(config)
