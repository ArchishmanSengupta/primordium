"""Configuration system for PRIMORDIUM."""

from primordium.config.schema import GenesisConfig
from primordium.config.loader import load_config, load_default_config, save_config
from primordium.config.defaults import DEFAULT_CONFIG

__all__ = [
    'GenesisConfig',
    'load_config',
    'load_default_config',
    'save_config',
    'DEFAULT_CONFIG',
]
