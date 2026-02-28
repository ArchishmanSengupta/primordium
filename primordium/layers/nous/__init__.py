"""NOUS: Intelligence layer.

Adds recursive self-modeling, meta-learning, and theory of mind.
Named after the Greek concept of intellect/reason - the highest cognitive faculty.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
from collections import deque


class SelfModel:
    """Model of the scroll's own behavior and capabilities."""

    def __init__(self):
        self.behavior_history = deque(maxlen=1000)
        self.capability_estimate = 0.0

    def record_behavior(self, steps: int, fitness: float):
        """Record behavior outcome."""
        self.behavior_history.append({
            'steps': steps,
            'fitness': fitness,
        })
        # Update capability estimate
        if self.behavior_history:
            recent = list(self.behavior_history)[-100:]
            self.capability_estimate = np.mean([b['fitness'] for b in recent])

    def get_model(self) -> Dict[str, float]:
        """Get current self-model."""
        return {
            'capability': self.capability_estimate,
            'behavior_count': len(self.behavior_history),
        }


class MetaLearner:
    """Meta-learning to improve learning algorithms."""

    def __init__(self, history_size: int = 1000):
        self.history_size = history_size
        self.epoch_improvements = deque(maxlen=history_size)

    def record_improvement(self, epoch: int, improvement: float):
        """Record improvement from an epoch."""
        self.epoch_improvements.append({
            'epoch': epoch,
            'improvement': improvement,
        })

    def get_best_strategy(self) -> Dict[str, Any]:
        """Get best learned strategy."""
        if not self.epoch_improvements:
            return {'strategy': 'none', 'confidence': 0.0}

        improvements = [e['improvement'] for e in self.epoch_improvements]
        avg_improvement = np.mean(improvements)

        if avg_improvement > 0.1:
            strategy = 'explore'
            confidence = min(avg_improvement, 1.0)
        elif avg_improvement > 0:
            strategy = 'exploit'
            confidence = min(avg_improvement, 1.0)
        else:
            strategy = 'reset'
            confidence = 0.5

        return {
            'strategy': strategy,
            'confidence': confidence,
            'avg_improvement': avg_improvement,
        }


class TheoryOfMind:
    """Model other scrolls' behavior."""

    def __init__(self, max_models: int = 100):
        self.max_models = max_models
        self.scroll_models = {}

    def update_model(self, scroll_id: str, steps: int, fitness: float):
        """Update model for a scroll."""
        if scroll_id not in self.scroll_models:
            self.scroll_models[scroll_id] = deque(maxlen=100)

        self.scroll_models[scroll_id].append({
            'steps': steps,
            'fitness': fitness,
        })

    def predict_behavior(self, scroll_id: str) -> Dict[str, float]:
        """Predict how a scroll will behave."""
        if scroll_id not in self.scroll_models or not self.scroll_models[scroll_id]:
            return {'predicted_fitness': 0.0, 'confidence': 0.0}

        history = list(self.scroll_models[scroll_id])
        avg_fitness = np.mean([h['fitness'] for h in history])
        variance = np.var([h['fitness'] for h in history])

        confidence = 1.0 / (1.0 + variance)

        return {
            'predicted_fitness': avg_fitness,
            'confidence': confidence,
        }

    def find_interesting_partners(self, my_id: str, top_k: int = 5) -> List[Dict]:
        """Find scrolls with interesting/complementary behavior."""
        predictions = []

        for scroll_id, history in self.scroll_models.items():
            if scroll_id == my_id:
                continue

            if not history:
                continue

            recent = list(history)[-10:]
            fitnesses = [h['fitness'] for h in recent]
            avg = np.mean(fitnesses)

            predictions.append({
                'scroll_id': scroll_id,
                'avg_fitness': avg,
                'variance': np.var(fitnesses),
            })

        # Sort by interestingness (high fitness, moderate variance)
        predictions.sort(key=lambda x: x['avg_fitness'] - 0.1 * x['variance'], reverse=True)

        return predictions[:top_k]


class NousLayer:
    """NOUS layer for recursive self-modeling and meta-learning.

    Adds:
    - Self-modeling (understanding own capabilities)
    - Meta-learning (learning to learn)
    - Theory of mind (modeling others)
    - Strategic planning
    """

    def __init__(self, config: Dict[str, Any]):
        self.enabled = config.get('enabled', True)

        # Self-modeling settings
        self.self_model_enabled = config.get('self_model_enabled', True)

        # Meta-learning settings
        self.meta_learn_enabled = config.get('meta_learn_enabled', True)
        self.strategy = 'balanced'  # explore/exploit

        # Theory of mind settings
        self.theory_of_mind_enabled = config.get('theory_of_mind_enabled', True)

        # Initialize components
        self.self_model = SelfModel()
        self.meta_learner = MetaLearner()
        self.theory_of_mind = TheoryOfMind()

        # Track previous epoch fitness for improvement calculation
        self.prev_epoch_avg_fitness = 0.0

    def before_interaction(self, soup, i: int, j: int) -> None:
        """Before interaction, use theory of mind to select partners."""
        if not self.enabled or not self.theory_of_mind_enabled:
            return

        # Could use theory of mind to select better interaction partners
        # For now, just track that interaction will happen
        pass

    def after_interaction(self, soup, i: int, j: int, steps: int) -> None:
        """After interaction, update models."""
        if not self.enabled:
            return

        scroll_i = soup.scrolls[i]
        scroll_j = soup.scrolls[j]

        # Update self-model
        if self.self_model_enabled:
            fitness_i = getattr(scroll_i, 'fitness', 0.0)
            fitness_j = getattr(scroll_j, 'fitness', 0.0)
            self.self_model.record_behavior(steps, fitness_i)

        # Update theory of mind
        if self.theory_of_mind_enabled:
            fitness_i = getattr(scroll_i, 'fitness', 0.0)
            fitness_j = getattr(scroll_j, 'fitness', 0.0)
            self.theory_of_mind.update_model(scroll_i.id, steps, fitness_i)
            self.theory_of_mind.update_model(scroll_j.id, steps, fitness_j)

    def after_epoch(self, soup, epoch: int) -> Dict[str, Any]:
        """After epoch, perform meta-learning and return stats."""
        if not self.enabled:
            return {}

        # Calculate improvement
        if soup.scrolls:
            current_avg = np.mean([s.fitness for s in soup.scrolls])
        else:
            current_avg = 0.0

        improvement = current_avg - self.prev_epoch_avg_fitness
        self.prev_epoch_avg_fitness = current_avg

        # Record for meta-learning
        if self.meta_learn_enabled:
            self.meta_learner.record_improvement(epoch, improvement)
            strategy = self.meta_learner.get_best_strategy()
            self.strategy = strategy['strategy']

        stats = {
            'nous_avg_fitness': current_avg,
            'nous_improvement': improvement,
            'nous_strategy': self.strategy,
        }

        # Self-model stats
        if self.self_model_enabled:
            model = self.self_model.get_model()
            stats['nous_self_capability'] = model['capability']

        # Theory of mind stats
        if self.theory_of_mind_enabled:
            stats['nous_models_tracked'] = len(self.theory_of_mind.scroll_models)

        return stats

    def get_self_model(self) -> Dict[str, float]:
        """Get current self-model."""
        if not self.self_model_enabled:
            return {}
        return self.self_model.get_model()

    def get_theory_predictions(self, scroll_id: str) -> Dict[str, float]:
        """Get theory of mind predictions for a scroll."""
        if not self.theory_of_mind_enabled:
            return {}
        return self.theory_of_mind.predict_behavior(scroll_id)

    def get_strategic_recommendation(self) -> str:
        """Get strategic recommendation based on meta-learning."""
        if not self.meta_learn_enabled:
            return 'balanced'
        strategy = self.meta_learner.get_best_strategy()
        return strategy['strategy']


def create_nous(config: Dict[str, Any]) -> NousLayer:
    """Factory function to create NOUS layer."""
    return NousLayer(config)
