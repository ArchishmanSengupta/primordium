"""Default configuration values for PRIMORDIUM."""

from typing import Dict, Any


DEFAULT_CONFIG: Dict[str, Any] = {
    "experiment": {
        "name": "default",
        "description": None,
        "seed": None,
        "output_dir": "./chronicle/{name}_{timestamp}",
        "resume_from": None,
    },
    "chaos": {
        "size": 256,
        "tape_length": 48,
        "initialisation": "random",
        "initial_instruction_density": 0.03,
    },
    "aether": {
        "backend": "python",
        "device": "cpu",
        "max_steps_per_interaction": 350,
        "interactions_total": 100000,
        "checkpoint_every": 10000,
    },
    "apeiron": {
        "rule": "standard",
        "selection": "uniform",
        "spatial_radius": None,
    },
    "layers": {
        "genesis": {
            "enabled": True,
            "track_phylogeny": True,
            "phylogeny_depth": 50,
        },
        "gaia": {
            "enabled": False,
            "spatial_topology": "flat",
            "grid_width": None,
            "grid_height": None,
            "migration_rate": 0.01,
            "resource_model": "fixed",
        },
        "hermes": {
            "enabled": False,
            "signal_bytes": 8,
            "signal_position": "head",
            "signal_decay": 0.0,
        },
        "mnemosyne": {
            "enabled": False,
            "register_size": 8,
            "memory_decay": 0.0,
        },
        "prometheus": {
            "enabled": False,
            "prediction_bonus": 1.0,
            "prediction_window": 10,
        },
        "nous": {
            "enabled": False,
            "modeling_depth": 3,
            "depth_bonus_scale": 1.5,
        },
    },
    "demiurge": {
        "enabled": False,
        "encoding_scheme": "direct",
        "max_layers": 10,
        "max_width": 256,
        "activation_set": ["relu", "tanh", "gelu", "sigmoid"],
        "eval_dataset": "mnist",
        "eval_samples": 1000,
        "eval_timeout_seconds": 30.0,
        "sandbox": True,
    },
    "kratos": {
        "fitness_function": "replication",
        "selection_pressure": 0.5,
        "elitism": 0.1,
    },
    "metrics": {
        "log_interval": 10000,
        "metrics_enabled": [
            "entropy",
            "instruction_density",
            "avg_ops_per_interaction",
            "top_replicators",
            "phase_detector",
            "complexity",
        ],
        "top_replicators_n": 10,
        "complexity_sample_size": 50,
    },
    "logging": {
        "level": "info",
        "format": "human",
        "live_display": True,
        "save_scroll_format": True,
    },
}
