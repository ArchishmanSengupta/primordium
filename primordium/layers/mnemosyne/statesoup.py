import numpy as np
from typing import Dict, Any, List
from collections import deque


def extract_state_features(scroll) -> np.ndarray:
    execution_steps = getattr(scroll, 'execution_steps', 0)
    branch_count = getattr(scroll, 'branch_count', 0)

    tape = getattr(scroll, 'tape', np.zeros(48, dtype=np.uint8))

    tape_mean = np.mean(tape) / 255.0
    tape_std = np.std(tape) / 255.0
    tape_entropy = -np.sum((np.bincount(tape, minlength=256) / len(tape) + 1e-10) *
                          np.log2(np.bincount(tape, minlength=256) / len(tape) + 1e-10))

    loop_count = np.sum(tape == 91) + np.sum(tape == 93)
    move_count = np.sum(tape == 62) + np.sum(tape == 60)
    modify_count = np.sum(tape == 43) + np.sum(tape == 45)

    features = [
        execution_steps / 1000.0,
        branch_count / 10.0,
        tape_mean,
        tape_std,
        tape_entropy / 8.0,
        loop_count / 10.0,
        move_count / 10.0,
        modify_count / 10.0,
    ]

    return np.array(features, dtype=np.float32)


class StateSoupMnemosyneLayer:
    def __init__(self, config: Dict[str, Any]):
        self.enabled = config.get('enabled', True)
        self.state_dim = config.get('state_dim', 32)
        self.max_task_states = config.get('max_task_states', 1000)
        self.store_frequency = config.get('store_frequency', 100)
        self.retrieve_enabled = config.get('retrieve_enabled', True)

        self.task_states = deque(maxlen=self.max_task_states)
        self.state_space = {}

        self.interaction_count = 0

    def store_task_state(self, epoch: int, state: np.ndarray, fitness: float) -> None:
        self.task_states.append({
            'epoch': epoch,
            'state': state,
            'fitness': fitness,
        })

    def linear_interpolate(self, state_a: np.ndarray, state_b: np.ndarray,
                          alpha: float = 0.5) -> np.ndarray:
        return alpha * state_a + (1 - alpha) * state_b

    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def retrieve_and_mix(self, query_state: np.ndarray, top_k: int = 3) -> np.ndarray:
        if not self.task_states:
            return query_state

        similarities = []
        for task in self.task_states:
            sim = self.cosine_similarity(query_state, task['state'])
            similarities.append((sim, task))

        similarities.sort(reverse=True, key=lambda x: x[0])
        top_states = [s[1]['state'] for s in similarities[:top_k]]

        if not top_states:
            return query_state

        return np.mean(top_states, axis=0)

    def after_interaction(self, soup, i: int, j: int, steps: int) -> None:
        if not self.enabled:
            return

        self.interaction_count += 1

        if self.interaction_count % self.store_frequency == 0:
            scroll_i = soup.scrolls[i]
            scroll_j = soup.scrolls[j]

            state_i = extract_state_features(scroll_i)
            state_j = extract_state_features(scroll_j)

            fitness_i = getattr(scroll_i, 'fitness', 0.0)
            fitness_j = getattr(scroll_j, 'fitness', 0.0)

            if fitness_i > 0.3:
                self.store_task_state(
                    epoch=self.interaction_count // self.store_frequency,
                    state=state_i,
                    fitness=fitness_i
                )

            if fitness_j > 0.3:
                self.store_task_state(
                    epoch=self.interaction_count // self.store_frequency,
                    state=state_j,
                    fitness=fitness_j
                )

    def after_epoch(self, soup, epoch: int) -> Dict[str, Any]:
        if not self.enabled:
            return {}

        if soup.scrolls:
            best_scroll = max(soup.scrolls, key=lambda s: getattr(s, 'fitness', 0.0))
            best_state = extract_state_features(best_scroll)
            best_fitness = getattr(best_scroll, 'fitness', 0.0)
            self.store_task_state(epoch=epoch, state=best_state, fitness=best_fitness)

        stats = {
            'statesoup_task_count': len(self.task_states),
            'statesoup_unique_epochs': len(set(t['epoch'] for t in self.task_states)),
        }

        return stats

    def retrieve_patterns(self, tape: np.ndarray, top_k: int = 5) -> List[Dict]:
        if not self.retrieve_enabled or not self.task_states:
            return []

        query_state = np.random.randn(self.state_dim)
        query_state[:8] = extract_state_features(type('Scroll', (), {'tape': tape, 'execution_steps': 0, 'branch_count': 0})())

        mixed_state = self.retrieve_and_mix(query_state, top_k)

        results = []
        for task in self.task_states:
            sim = self.cosine_similarity(mixed_state, task['state'])
            results.append({'state': task['state'], 'fitness': task['fitness'], 'similarity': sim})

        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]


def create_statesoup_mnemosyne(config: Dict[str, Any]) -> StateSoupMnemosyneLayer:
    return StateSoupMnemosyneLayer(config)
