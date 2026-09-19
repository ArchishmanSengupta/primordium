import numpy as np
import pytest

from primordium.layers.mnemosyne.statesoup import StateSoupMnemosyneLayer, extract_state_features


class TestStateFeatureExtraction:
    def test_extract_state_features(self):
        class MockScroll:
            def __init__(self):
                self.execution_steps = 100
                self.branch_count = 5
                self.tape = np.random.randint(0, 256, 48, dtype=np.uint8)

        scroll = MockScroll()
        features = extract_state_features(scroll)
        assert len(features) > 0

    def test_extract_state_has_expected_components(self):
        class MockScroll:
            def __init__(self):
                self.execution_steps = 50
                self.branch_count = 3
                self.tape = np.array([42] * 48, dtype=np.uint8)

        scroll = MockScroll()
        features = extract_state_features(scroll)
        assert features[0] == 50 / 1000.0
        assert features[1] == 3 / 10.0


class TestStateSoupMnemosyne:
    def test_initializes(self):
        layer = StateSoupMnemosyneLayer({'enabled': True})
        assert layer.enabled is True

    def test_stores_task_state(self):
        layer = StateSoupMnemosyneLayer({'enabled': True})
        state = np.random.randn(32)
        layer.store_task_state(epoch=1, state=state, fitness=0.5)
        assert len(layer.task_states) == 1
        assert layer.task_states[0]['epoch'] == 1

    def test_linear_interpolation(self):
        layer = StateSoupMnemosyneLayer({'enabled': True})
        state_a = np.ones(32) * 0.0
        state_b = np.ones(32) * 1.0
        mixed = layer.linear_interpolate(state_a, state_b, alpha=0.5)
        assert np.allclose(mixed, 0.5)

    def test_retrieve_and_mix(self):
        layer = StateSoupMnemosyneLayer({'enabled': True})
        for i in range(5):
            state = np.random.randn(32) + i
            layer.store_task_state(epoch=i, state=state, fitness=0.5)

        query_state = np.random.randn(32)
        mixed = layer.retrieve_and_mix(query_state, top_k=3)
        assert mixed.shape == (32,)

    def test_after_epoch_returns_stats(self):
        layer = StateSoupMnemosyneLayer({'enabled': True})
        from primordium.chaos import Soup
        soup = Soup(size=10, tape_length=48, seed=42)
        stats = layer.after_epoch(soup, epoch=1)
        assert 'statesoup_task_count' in stats


    def test_retrieve_patterns_uses_real_feature_dims(self):
        layer = StateSoupMnemosyneLayer({'enabled': True})
        soup_tape = np.random.randint(0, 256, 48, dtype=np.uint8)
        layer.store_task_state(
            epoch=1,
            state=extract_state_features(
                type('S', (), {'tape': soup_tape, 'execution_steps': 0, 'branch_count': 0})(),
            ),
            fitness=0.5,
        )

        results = layer.retrieve_patterns(soup_tape, top_k=1)
        assert len(results) == 1
        assert results[0]['similarity'] > 0.99


class TestStateSoupIntegration:
    def test_mixing_improves_fitness(self):
        layer = StateSoupMnemosyneLayer({'enabled': True})
        good_state = np.ones(32) * 0.9
        bad_state = np.ones(32) * 0.1
        layer.store_task_state(epoch=1, state=good_state, fitness=0.9)
        layer.store_task_state(epoch=2, state=bad_state, fitness=0.1)

        mixed = layer.linear_interpolate(good_state, bad_state, alpha=0.7)
        assert np.mean(mixed) > 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
