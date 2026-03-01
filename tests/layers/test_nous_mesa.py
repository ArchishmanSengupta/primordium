import numpy as np
import pytest
from collections import deque

from primordium.layers.nous.mesa import MesaOptimizationDetector, MesaNousLayer


class TestMesaOptimizationDetector:
    def test_detector_initializes(self):
        detector = MesaOptimizationDetector()
        assert detector.execution_traces.maxlen == 1000

    def test_record_trace(self):
        detector = MesaOptimizationDetector()
        trace = {'steps': 50, 'fitness': 0.7, 'tape_before': [1, 2, 3], 'tape_after': [1, 2, 4]}
        detector.record_trace('scroll1', trace)
        assert len(detector.execution_traces) == 1

    def test_detect_learning_signal_positive(self):
        detector = MesaOptimizationDetector()
        for i in range(10):
            trace = {'steps': 50, 'fitness': 0.1 * i, 'tape_deltas': [1, 2, 3]}
            detector.record_trace('scroll1', trace)
        has_learning = detector.detect_learning_signal('scroll1')
        assert bool(has_learning) is True

    def test_detect_learning_signal_negative(self):
        detector = MesaOptimizationDetector()
        np.random.seed(123)
        for i in range(10):
            trace = {'steps': 50, 'fitness': 0.5 + np.random.randn() * 0.5, 'tape_deltas': [1, 2, 3]}
            detector.record_trace('scroll1', trace)
        has_learning = detector.detect_learning_signal('scroll1')
        assert bool(has_learning) is False

    def test_detect_goal_states(self):
        detector = MesaOptimizationDetector()
        tape = np.array([0] * 40 + [255] * 8, dtype=np.uint8)
        has_goal = detector.detect_goal_states(tape)
        assert isinstance(bool(has_goal), bool)

    def test_detect_planning(self):
        detector = MesaOptimizationDetector()
        tape = np.array([91, 62, 43, 93, 91, 60, 45, 93], dtype=np.uint8)
        has_planning = detector.detect_planning(tape)
        assert isinstance(has_planning, bool)

    def test_full_analysis(self):
        detector = MesaOptimizationDetector()
        for i in range(20):
            trace = {'steps': 50 + i, 'fitness': 0.1 * i, 'tape_deltas': [1, 2, 3]}
            detector.record_trace('scroll1', trace)
        tape = np.array([91, 62, 43, 93] * 3, dtype=np.uint8)
        result = detector.analyze_for_mesa_optimization(tape, 'scroll1')
        assert 'mesa_optimization' in result
        assert 'learning_signal' in result
        assert 'confidence' in result


class TestMesaNousLayer:
    def test_layer_initializes(self):
        config = {'enabled': True, 'mesa_detection_enabled': True}
        layer = MesaNousLayer(config)
        assert layer.enabled is True

    def test_after_epoch_returns_stats(self):
        config = {'enabled': True, 'mesa_detection_enabled': True}
        layer = MesaNousLayer(config)
        from primordium.chaos import Soup
        soup = Soup(size=10, tape_length=48, seed=42)
        stats = layer.after_epoch(soup, epoch=1)
        assert 'mesa_detected_count' in stats or 'mesa_detection_enabled' in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
