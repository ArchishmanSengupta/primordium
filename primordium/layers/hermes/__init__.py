"""HERMES: Messenger layer.

Implements error correction, signal propagation, and inter-layer communication.
Named after the Greek messenger god - handles communication and translation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
from collections import deque


class ErrorCorrector:
    """Detect and correct errors in BF programs."""

    def __init__(self):
        self.corrected_count = 0

    def check_bracket_balance(self, tape: np.ndarray) -> bool:
        """Check if brackets are balanced.

        Args:
            tape: BF tape to check

        Returns:
            True if balanced
        """
        if len(tape) == 0:
            return True
        bal = np.cumsum((tape == 91).astype(np.int64) - (tape == 93).astype(np.int64))
        return bool(bal[-1] == 0 and bal.min() >= 0)

    def correct_bracket_imbalance(self, tape: np.ndarray) -> np.ndarray:
        """Repair bracket structure so loops can execute.

        Neutralizes any ']' that opens before its matching '[', then closes
        leftover unmatched '[' by overwriting the byte that follows it.

        Args:
            tape: BF tape to correct

        Returns:
            Corrected tape
        """
        if self.check_bracket_balance(tape):
            return tape

        corrected = tape.copy()
        changed = False

        balance = 0
        for i in range(len(corrected)):
            if corrected[i] == 91:
                balance += 1
            elif corrected[i] == 93:
                if balance == 0:
                    corrected[i] = 0
                    changed = True
                else:
                    balance -= 1

        for _ in range(len(corrected)):
            stack = []
            for i in range(len(corrected)):
                if corrected[i] == 91:
                    stack.append(i)
                elif corrected[i] == 93 and stack:
                    stack.pop()
            if not stack:
                break
            insert_pos = stack[-1] + 1
            if insert_pos >= len(corrected):
                corrected[stack[-1]] = 0
            else:
                corrected[insert_pos] = 93
            changed = True

        if changed:
            self.corrected_count += 1
        return corrected


class SignalPropagator:
    """Propagate signals/messages between scrolls."""

    def __init__(self, buffer_size: int = 1000):
        self.buffer_size = buffer_size
        self.signal_buffer = deque(maxlen=buffer_size)

    def emit_signal(self, source_id: str, signal_type: str, data: Any):
        """Emit a signal from a scroll."""
        self.signal_buffer.append({
            'source': source_id,
            'type': signal_type,
            'data': data,
        })

    def get_signals(self, scroll_id: Optional[str] = None, signal_type: Optional[str] = None) -> List[Dict]:
        """Get signals matching criteria."""
        results = list(self.signal_buffer)

        if scroll_id:
            results = [s for s in results if s['source'] == scroll_id]

        if signal_type:
            results = [s for s in results if s['type'] == signal_type]

        return results


class HermesLayer:
    """HERMES layer for error correction and message passing."""

    def __init__(self, config: Dict[str, Any]):
        self.enabled = config.get('enabled', True)
        self.auto_correct = config.get('auto_correct', True)
        self.correct_bracket_balance = config.get('correct_bracket_balance', True)
        self.enable_signals = config.get('enable_signals', True)
        self.signal_buffer_size = config.get('signal_buffer_size', 1000)

        self.error_corrector = ErrorCorrector()
        self.signal_propagator = SignalPropagator(self.signal_buffer_size)

    def before_interaction(self, soup, i: int, j: int) -> None:
        """Before interaction, validate and correct programs."""
        if not self.enabled:
            return

        if self.correct_bracket_balance and self.auto_correct:
            scroll_i = soup.scrolls[i]
            scroll_j = soup.scrolls[j]

            if not self.error_corrector.check_bracket_balance(scroll_i.tape):
                soup.scrolls[i].tape = self.error_corrector.correct_bracket_imbalance(
                    scroll_i.tape
                )

            if not self.error_corrector.check_bracket_balance(scroll_j.tape):
                soup.scrolls[j].tape = self.error_corrector.correct_bracket_imbalance(
                    scroll_j.tape
                )

    def after_interaction(self, soup, i: int, j: int, steps: int) -> None:
        """After interaction, emit signals about program quality."""
        if not self.enabled or not self.enable_signals:
            return

        scroll_i = soup.scrolls[i]
        scroll_j = soup.scrolls[j]

        quality_i = self._compute_quality(scroll_i.tape)
        quality_j = self._compute_quality(scroll_j.tape)

        self.signal_propagator.emit_signal(
            scroll_i.id, 'quality', {'value': quality_i, 'steps': steps}
        )
        self.signal_propagator.emit_signal(
            scroll_j.id, 'quality', {'value': quality_j, 'steps': steps}
        )

    def _compute_quality(self, tape: np.ndarray) -> float:
        """Compute quality metric for a tape."""
        unique_values = len(np.unique(tape))
        valid_ops = np.sum(np.isin(tape, [62, 60, 43, 45, 91, 93, 46]))
        density = valid_ops / len(tape)
        balanced = self.error_corrector.check_bracket_balance(tape)
        balance_score = 1.0 if balanced else 0.0

        quality = (
            0.3 * (unique_values / 256) +
            0.4 * density +
            0.3 * balance_score
        )

        return quality

    def after_epoch(self, soup, epoch: int) -> Dict[str, Any]:
        """After epoch, return error correction statistics."""
        if not self.enabled:
            return {}

        return {
            'hermes_corrections': self.error_corrector.corrected_count,
            'hermes_signal_buffer_size': len(self.signal_propagator.signal_buffer),
        }

    def get_signals(self, scroll_id: Optional[str] = None, signal_type: Optional[str] = None) -> List[Dict]:
        """Get signals from buffer."""
        return self.signal_propagator.get_signals(scroll_id, signal_type)


def create_hermes(config: Dict[str, Any]) -> HermesLayer:
    """Factory function to create HERMES layer."""
    return HermesLayer(config)
