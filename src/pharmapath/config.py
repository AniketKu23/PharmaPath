"""
Configuration loader and validator for PharmaPath.
"""

from pathlib import Path
from typing import Any, Dict
import yaml


def get_project_root() -> Path:
    """Return the root path of the project."""
    return Path(__file__).resolve().parent.parent.parent


def load_yaml(filepath: Path | str) -> Dict[str, Any]:
    """Load and parse a YAML file."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_params(config_path: Path | str | None = None) -> Dict[str, Any]:
    """Load global pipeline parameters."""
    if config_path is None:
        config_path = get_project_root() / "config" / "params.yaml"
    return load_yaml(config_path)


def load_drugs_config(config_path: Path | str | None = None) -> Dict[str, Any]:
    """Load drug specifications."""
    if config_path is None:
        config_path = get_project_root() / "config" / "drugs.yaml"
    return load_yaml(config_path)
