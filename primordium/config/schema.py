"""Configuration schema for PRIMORDIUM.

This module defines the Pydantic models that validate experiment configurations.

DESIGN PHILOSOPHY
=================

PRIMORDIUM is based on Blaise Agüera y Arcas's BFF experiment (arXiv:2406.19108),
which demonstrated that life and purpose emerge from pure computation through
symbiogenesis (merger) - WITHOUT mutation and WITHOUT fitness functions.

PHASE 1: Core Foundation
------------------------
The core soup dynamics use UNIFORM RANDOM SELECTION, not fitness-based selection.
This is intentional - the BFF experiment proves emergence happens through
thermodynamic selection (programs that copy get copied more) alone.

KRATOS - Fitness Configuration
-----------------------------
Fitness functions do NOT belong in the core soup dynamics (Phases 1-6).
They are only valid for DEMIURGE architecture evaluation, where you must
measure whether a decoded neural network performs a task.

Layer Build Order
-----------------
All layers are DISABLED by default. The correct order is:
- Phase 1: AETHER, CHAOS, METRICS (core - demonstrate phase transition first)
- Phase 2: GAIA (spatial ecology - based on Figure 8 of arXiv:2406.19108)
- Phase 3-6: HERMES, MNEMOSYNE, PROMETHEUS, NOUS (defer based on what emerges)
- Phase 7+: DEMIURGE (neural encoding - requires sufficient complexity)

See FOUNDATION.md "Recommended Build Order" for full details.
"""

from __future__ import annotations

from typing import Optional, List, Literal, Dict
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class ExperimentConfig(BaseModel):
    """Experiment-level configuration."""
    name: str = Field(..., description="Experiment name, used for output directory")
    description: Optional[str] = Field(None, description="Optional description")
    seed: Optional[int] = Field(None, description="Random seed (null = random)")
    output_dir: str = Field(
        "./chronicle/{name}_{timestamp}",
        description="Output directory path"
    )
    resume_from: Optional[str] = Field(None, description="Path to checkpoint to resume from")


class ChaosConfig(BaseModel):
    """CHAOS soup configuration."""
    size: int = Field(256, description="Number of scrolls in the soup")
    tape_length: int = Field(48, description="Bytes per scroll")
    initialisation: Literal["random", "structured", "seeded"] = Field(
        "random",
        description="Initialization method"
    )
    initial_instruction_density: float = Field(
        0.03,
        description="Instruction density for structured initialization"
    )


class AetherConfig(BaseModel):
    """AETHER engine configuration."""
    backend: Literal["python", "c", "cuda"] = Field(
        "python",
        description="Which implementation to use"
    )
    device: str = Field("cpu", description="Device for CUDA backend")
    max_steps_per_interaction: int = Field(
        350,
        description="Maximum steps per interaction"
    )
    interactions_total: int = Field(
        100000,
        description="Total interactions to run"
    )
    checkpoint_every: int = Field(
        10000,
        description="Save checkpoint every N interactions"
    )


class ApeironConfig(BaseModel):
    """APEIRON interaction rule configuration."""
    rule: str = Field("standard", description="Interaction rule name")
    selection: Literal["uniform", "spatial", "fitness_biased"] = Field(
        "uniform",
        description="Selection method for pairs"
    )
    spatial_radius: Optional[int] = Field(
        None,
        description="Radius for spatial selection"
    )


class GenesisLayerConfig(BaseModel):
    """GENESIS layer configuration."""
    # PHASE 1: Disabled by default. Enable after phase transition confirmed.
    enabled: bool = Field(False, description="Genesis layer enabled")
    track_phylogeny: bool = Field(True, description="Track ancestry")
    phylogeny_depth: int = Field(50, description="Depth to track ancestry")


class GaiaLayerConfig(BaseModel):
    """GAIA layer configuration."""
    enabled: bool = Field(False, description="Gaia layer enabled")
    spatial_topology: Literal["flat", "grid", "toroidal"] = Field(
        "flat",
        description="Spatial topology"
    )
    grid_width: Optional[int] = Field(None, description="Grid width")
    grid_height: Optional[int] = Field(None, description="Grid height")
    migration_rate: float = Field(0.01, description="Long-range interaction probability")
    resource_model: Literal["fixed", "dynamic"] = Field("fixed", description="Resource model")


class HermesLayerConfig(BaseModel):
    """HERMES layer configuration."""
    enabled: bool = Field(False, description="Hermes layer enabled")
    signal_bytes: int = Field(8, description="Bytes reserved for signals")
    signal_position: Literal["head", "tail"] = Field("head", description="Signal position on tape")
    signal_decay: float = Field(0.0, description="Signal decay rate")


class MnemosyneLayerConfig(BaseModel):
    """MNEMOSYNE layer configuration."""
    enabled: bool = Field(False, description="Mnemosyne layer enabled")
    register_size: int = Field(8, description="Persistent memory bytes per scroll")
    memory_decay: float = Field(0.0, description="Memory byte clearing probability")


class PrometheusLayerConfig(BaseModel):
    """PROMETHEUS layer configuration.

    WARNING: The prediction_bonus mechanism crosses from substrate provision
    into behavioral nudging. If prediction is genuinely adaptive, programs
    will evolve it without any bonus. This mechanism may need redesign.

    See FOUNDATION.md "Recommended Build Order" - defer to Phase 5+.
    """
    enabled: bool = Field(False, description="Prometheus layer enabled")
    prediction_bonus: float = Field(
        1.0,
        description="[DEPRECATED] Replication multiplier for accurate prediction - redesign required"
    )
    prediction_window: int = Field(10, description="Past interactions for prediction")


class NousLayerConfig(BaseModel):
    """NOUS layer configuration.

    Theory of mind and meta-cognition per Agüera y Arcas (ALIFE 2025).
    This is the correct long-term research target but requires ecologically
    differentiated, communicating programs to be meaningful.

    See FOUNDATION.md "Recommended Build Order" - defer to Phase 6+.
    """
    enabled: bool = Field(False, description="Nous layer enabled")
    modeling_depth: int = Field(3, description="Max recursive modeling depth")
    depth_bonus_scale: float = Field(1.5, description="Bonus multiplier per depth level")


class LayersConfig(BaseModel):
    """All evolutionary layers configuration."""
    genesis: GenesisLayerConfig = Field(default_factory=GenesisLayerConfig)
    gaia: GaiaLayerConfig = Field(default_factory=GaiaLayerConfig)
    hermes: HermesLayerConfig = Field(default_factory=HermesLayerConfig)
    mnemosyne: MnemosyneLayerConfig = Field(default_factory=MnemosyneLayerConfig)
    prometheus: PrometheusLayerConfig = Field(default_factory=PrometheusLayerConfig)
    nous: NousLayerConfig = Field(default_factory=NousLayerConfig)


class DemiurgeConfig(BaseModel):
    """DEMIURGE neural encoding configuration."""
    enabled: bool = Field(False, description="Demiurge layer enabled")
    encoding_scheme: Literal["direct", "indirect", "developmental"] = Field(
        "direct",
        description="Neural architecture encoding scheme"
    )
    max_layers: int = Field(10, description="Max layers in encoded architectures")
    max_width: int = Field(256, description="Max neurons per layer")
    activation_set: List[str] = Field(
        default_factory=lambda: ["relu", "tanh", "gelu", "sigmoid"],
        description="Available activation functions"
    )
    eval_dataset: str = Field("mnist", description="Dataset for evaluation")
    eval_samples: int = Field(1000, description="Samples per evaluation")
    eval_timeout_seconds: float = Field(30.0, description="Max evaluation time")
    sandbox: bool = Field(True, description="Run evaluations in subprocess sandbox")


class KratosConfig(BaseModel):
    """KRATOS fitness and selection configuration.

    IMPORTANT: Fitness functions do NOT belong in core soup dynamics.
    The BFF experiment proves emergence happens without fitness pressure.
    Thermodynamic selection (programs that copy get copied more) is sufficient.

    Fitness signals ARE valid ONLY for DEMIURGE architecture evaluation.
    """
    fitness_function: str = Field("replication", description="Fitness function name")
    selection_pressure: float = Field(
        0.5,
        description="How strongly fit scrolls outcompete (0.0 to 1.0)"
    )
    elitism: float = Field(0.1, description="Fraction of top scrolls protected")


class MetricsConfig(BaseModel):
    """Metrics configuration."""
    log_interval: int = Field(10000, description="Log every N interactions")
    metrics_enabled: List[str] = Field(
        default_factory=lambda: [
            "entropy",
            "instruction_density",
            "avg_ops_per_interaction",
            "top_replicators",
            "phase_detector",
            "complexity",
            "compression_ratio",  # Key for detecting phase transitions
            "life_criteria",  # Operational definition of life
        ],
        description="List of enabled metrics"
    )
    top_replicators_n: int = Field(10, description="Top replicators to track")
    complexity_sample_size: int = Field(50, description="Scrolls to sample for complexity")
    life_criteria_thresholds: Optional[Dict[str, float]] = Field(
        default_factory=lambda: {
            "instruction_density": 0.1,
            "replicator_fraction": 0.05,
            "compression_ratio": 0.8,
        },
        description="Thresholds for life criteria detection"
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: Literal["debug", "info", "warning", "error"] = Field("info", description="Log level")
    format: Literal["human", "json"] = Field("human", description="Log format")
    live_display: bool = Field(True, description="Show live terminal dashboard")
    save_scroll_format: bool = Field(True, description="Save full soup state at checkpoints")


class GenesisConfig(BaseModel):
    """Master configuration for PRIMORDIUM."""
    experiment: ExperimentConfig
    chaos: ChaosConfig = Field(default_factory=ChaosConfig)
    aether: AetherConfig = Field(default_factory=AetherConfig)
    apeiron: ApeironConfig = Field(default_factory=ApeironConfig)
    layers: LayersConfig = Field(default_factory=LayersConfig)
    demiurge: DemiurgeConfig = Field(default_factory=DemiurgeConfig)
    kratos: KratosConfig = Field(default_factory=KratosConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
