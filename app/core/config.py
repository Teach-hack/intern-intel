"""Application configuration loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

import yaml

_SETTINGS_PATH = Path(__file__).resolve().parent.parent / "config" / "settings.yaml"


def _read_settings() -> dict[str, Any]:
    """Load and validate settings from the YAML configuration file.

    Returns:
        The parsed settings dictionary.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        ValueError: If the configuration file is empty or not a mapping.
        yaml.YAMLError: If the configuration file contains invalid YAML.
    """
    if not _SETTINGS_PATH.is_file():
        raise FileNotFoundError(f"Configuration file not found: {_SETTINGS_PATH}")

    try:
        with _SETTINGS_PATH.open(encoding="utf-8") as settings_file:
            settings = yaml.safe_load(settings_file)
    except yaml.YAMLError as exc:
        raise yaml.YAMLError(
            f"Invalid YAML in configuration file {_SETTINGS_PATH}: {exc}"
        ) from exc

    if not isinstance(settings, dict):
        raise ValueError(
            f"Configuration file must contain a YAML mapping: {_SETTINGS_PATH}"
        )

    return settings


class Config:
    """Singleton configuration loader for application settings.

    Settings are read from ``app/config/settings.yaml`` on first use and cached
    until :meth:`reload` is called.
    """

    _instance: ClassVar[Config | None] = None
    _settings: dict[str, Any]

    def __new__(cls) -> Config:
        """Create or return the singleton instance."""
        if cls._instance is None:
            instance = super().__new__(cls)
            cls._instance = instance
            instance._settings = _read_settings()
        return cls._instance

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a configuration value using dot notation.

        Args:
            key: Nested configuration key, for example ``database.path``.
            default: Value to return when the key is missing.

        Returns:
            The configuration value, or ``default`` if the key is not found.
        """
        data: Any = self._settings
        for part in key.split("."):
            if not isinstance(data, dict) or part not in data:
                return default
            data = data[part]
        return data

    def reload(self) -> None:
        """Reload settings from the configuration file.

        Raises:
            FileNotFoundError: If the configuration file does not exist.
            ValueError: If the configuration file is empty or not a mapping.
            yaml.YAMLError: If the configuration file contains invalid YAML.
        """
        self._settings = _read_settings()


settings = Config()
