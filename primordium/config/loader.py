"""Configuration loader for PRIMORDIUM.

This module loads and validates genesis.yaml files.
"""

from __future__ import annotations

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from primordium.config.schema import GenesisConfig

logger = logging.getLogger(__name__)


def load_config(path: str) -> GenesisConfig:
    """Load configuration from a YAML file.

    Args:
        path: Path to genesis.yaml file

    Returns:
        Validated GenesisConfig

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, 'r') as f:
        data = yaml.safe_load(f)

    if data is None:
        data = {}

    # Handle output_dir template
    if 'experiment' not in data:
        data['experiment'] = {}

    if 'name' not in data['experiment']:
        data['experiment']['name'] = 'unnamed'

    name = data['experiment']['name']
    output_dir = data['experiment'].get('output_dir', './chronicle/{name}_{timestamp}')

    # Replace template variables
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = output_dir.replace('{name}', name)
    output_dir = output_dir.replace('{timestamp}', timestamp)
    data['experiment']['output_dir'] = output_dir

    # Validate and create config
    try:
        config = GenesisConfig(**data)
        logger.info(f"Loaded config from {path}")
        logger.info(f"Experiment: {config.experiment.name}")
        logger.info(f"Output directory: {config.experiment.output_dir}")
        return config
    except Exception as e:
        logger.error(f"Invalid config: {e}")
        raise ValueError(f"Invalid configuration: {e}")


def load_default_config() -> GenesisConfig:
    """Load default configuration.

    Returns:
        Default GenesisConfig
    """
    return GenesisConfig(
        experiment={
            'name': 'default',
            'output_dir': './chronicle/default',
        }
    )


def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two config dictionaries.

    Args:
        base: Base configuration
        override: Override configuration

    Returns:
        Merged configuration
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value

    return result


def save_config(config: GenesisConfig, path: str) -> None:
    """Save configuration to a YAML file.

    Args:
        config: Configuration to save
        path: Path to save to
    """
    # Convert to dict, excluding computed fields
    data = config.model_dump()

    # Ensure output directory exists
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)

    with open(path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Saved config to {path}")
