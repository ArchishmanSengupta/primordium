import numpy as np
import pytest

try:
    import torch
except ImportError:
    pytest.skip("PyTorch not available", allow_module_level=True)

from primordium.layers.demiurge.difflogic import DiffLogicBFEncoder, DiffLogicDemiurgeLayer


class TestDiffLogicBFEncoder:
    def test_encoder_initializes_on_mps_or_cpu(self):
        device = 'mps' if torch.backends.mps.is_available() else 'cpu'
        encoder = DiffLogicBFEncoder(tape_length=48, hidden_size=32, device=device)
        assert encoder is not None
        assert encoder.gate_logits.shape == (48, 16)

    def test_encoder_forward_no_crash(self):
        device = 'mps' if torch.backends.mps.is_available() else 'cpu'
        encoder = DiffLogicBFEncoder(tape_length=48, hidden_size=32, device=device)
        x = torch.randn(4, 48, device=device)
        output = encoder(x)
        assert output.shape == (4, 32)

    def test_gate_probabilities_sum_to_one(self):
        device = 'mps' if torch.backends.mps.is_available() else 'cpu'
        encoder = DiffLogicBFEncoder(tape_length=48, hidden_size=32, device=device)
        gate_probs = encoder.get_gate_probs()
        assert gate_probs.shape == (48, 16)
        assert torch.allclose(gate_probs.sum(dim=-1), torch.ones(48, device=device), atol=1e-5)

    def test_tape_encoding_roundtrip(self):
        device = 'mps' if torch.backends.mps.is_available() else 'cpu'
        encoder = DiffLogicBFEncoder(tape_length=48, hidden_size=32, device=device)
        tape = np.random.randint(0, 256, 48, dtype=np.uint8)
        weights = encoder.encode_tape(tape)
        assert weights.shape == (32, 48)


class TestDiffLogicDemiurgeLayer:
    def test_layer_initializes(self):
        config = {'enabled': True, 'tape_length': 48, 'hidden_size': 32}
        layer = DiffLogicDemiurgeLayer(config)
        assert layer.enabled is True

    def test_evaluate_scroll_returns_fitness(self):
        config = {'enabled': True, 'tape_length': 48, 'hidden_size': 32}
        layer = DiffLogicDemiurgeLayer(config)
        tape = np.random.randint(0, 256, 48, dtype=np.uint8)
        fitness = layer.evaluate_scroll(tape)
        assert 0.0 <= fitness <= 1.0

    def test_after_epoch_returns_stats(self):
        config = {'enabled': True, 'tape_length': 48, 'hidden_size': 32}
        layer = DiffLogicDemiurgeLayer(config)
        from primordium.chaos import Soup
        soup = Soup(size=10, tape_length=48, seed=42)
        stats = layer.after_epoch(soup, epoch=1)
        assert 'fitness_mean' in stats
        assert 'fitness_std' in stats


class TestDiffLogicFaultTolerance:
    def test_noisy_input_produces_stable_output(self):
        device = 'mps' if torch.backends.mps.is_available() else 'cpu'
        encoder = DiffLogicBFEncoder(tape_length=48, hidden_size=32, device=device)
        x = torch.randn(1, 48, device=device)
        output1 = encoder(x).clone()
        output2 = encoder(x + torch.randn_like(x) * 0.01).clone()
        diff = (output1 - output2).abs().mean().item()
        assert diff < 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
