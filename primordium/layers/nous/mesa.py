import numpy as np
from typing import Dict, Any, List
from collections import deque


class MesaOptimizationDetector:
    def __init__(self, max_traces: int = 1000):
        self.max_traces = max_traces
        self.execution_traces = deque(maxlen=max_traces)
        self.trace_history = {}

    def record_trace(self, scroll_id: str, trace: Dict) -> None:
        self.execution_traces.append((scroll_id, trace))
        if scroll_id not in self.trace_history:
            self.trace_history[scroll_id] = deque(maxlen=100)
        self.trace_history[scroll_id].append(trace)

    def get_traces_for_scroll(self, scroll_id: str) -> List[Dict]:
        if scroll_id in self.trace_history:
            return list(self.trace_history[scroll_id])
        return []

    def detect_learning_signal(self, scroll_id: str) -> bool:
        traces = self.get_traces_for_scroll(scroll_id)
        if len(traces) < 5:
            return False

        fitnesses = [t.get('fitness', 0) for t in traces]
        if not fitnesses:
            return False

        x = np.arange(len(fitnesses))
        y = np.array(fitnesses)
        try:
            slope, _ = np.polyfit(x, y, 1)
        except Exception:
            return False

        residuals = y - (slope * x + y[0])
        variance = np.var(residuals)

        return slope > 0.01 and variance < 0.1

    def detect_goal_states(self, tape: np.ndarray) -> bool:
        if len(tape) < 16:
            return False

        non_zero_ratio = np.count_nonzero(tape) / len(tape)
        if non_zero_ratio < 0.1:
            return False

        pattern = tape[:8]
        same_at_end = np.array_equal(pattern, tape[-8:])
        if same_at_end:
            return True

        high_bits = np.sum(tape > 127)
        return high_bits >= 4

    def detect_planning(self, tape: np.ndarray) -> bool:
        loop_starts = np.sum(tape == 91)
        loop_ends = np.sum(tape == 93)

        if loop_starts == 0 or loop_ends == 0:
            return False

        if abs(loop_starts - loop_ends) > 2:
            return False

        depth = 0
        max_depth = 0
        for byte in tape:
            if byte == 91:
                depth += 1
                max_depth = max(max_depth, depth)
            elif byte == 93:
                depth -= 1

        return max_depth >= 2

    def analyze_for_mesa_optimization(self, tape: np.ndarray, scroll_id: str) -> Dict[str, Any]:
        has_learning = self.detect_learning_signal(scroll_id)
        has_goals = self.detect_goal_states(tape)
        has_planning = self.detect_planning(tape)

        traces = self.get_traces_for_scroll(scroll_id)
        confidence = min(len(traces) / 20.0, 1.0) if traces else 0.0

        return {
            'mesa_optimization': has_learning and has_goals,
            'learning_signal': has_learning,
            'goal_representation': has_goals,
            'planning': has_planning,
            'confidence': confidence,
        }


class MesaNousLayer:
    def __init__(self, config: Dict[str, Any]):
        self.enabled = config.get('enabled', True)
        self.mesa_detection_enabled = config.get('mesa_detection_enabled', True)
        self.self_model_enabled = config.get('self_model_enabled', True)
        self.meta_learn_enabled = config.get('meta_learn_enabled', True)
        self.theory_of_mind_enabled = config.get('theory_of_mind_enabled', True)

        if self.mesa_detection_enabled:
            self.mesa_detector = MesaOptimizationDetector()
        else:
            self.mesa_detector = None

        self.prev_epoch_avg_fitness = 0.0

    def before_interaction(self, soup, i: int, j: int) -> None:
        pass

    def after_interaction(self, soup, i: int, j: int, steps: int) -> None:
        if not self.enabled or not self.mesa_detection_enabled:
            return

        scroll_i = soup.scrolls[i]
        scroll_j = soup.scrolls[j]

        fitness_i = getattr(scroll_i, 'fitness', 0.0)
        fitness_j = getattr(scroll_j, 'fitness', 0.0)

        trace_i = {'steps': steps, 'fitness': fitness_i, 'tape_deltas': [0, 0, 0]}
        trace_j = {'steps': steps, 'fitness': fitness_j, 'tape_deltas': [0, 0, 0]}

        self.mesa_detector.record_trace(scroll_i.id, trace_i)
        self.mesa_detector.record_trace(scroll_j.id, trace_j)

    def after_epoch(self, soup, epoch: int) -> Dict[str, Any]:
        if not self.enabled:
            return {}

        if soup.scrolls:
            current_avg = np.mean([s.fitness for s in soup.scrolls])
        else:
            current_avg = 0.0

        improvement = current_avg - self.prev_epoch_avg_fitness
        self.prev_epoch_avg_fitness = current_avg

        stats = {
            'nous_avg_fitness': current_avg,
            'nous_improvement': improvement,
            'mesa_detection_enabled': self.mesa_detection_enabled,
        }

        if self.mesa_detection_enabled and self.mesa_detector:
            mesa_count = 0
            for scroll in soup.scrolls:
                result = self.mesa_detector.analyze_for_mesa_optimization(scroll.tape, scroll.id)
                if result.get('mesa_optimization', False):
                    mesa_count += 1
            stats['mesa_detected_count'] = mesa_count

        return stats


def create_mesa_nous(config: Dict[str, Any]) -> MesaNousLayer:
    return MesaNousLayer(config)
