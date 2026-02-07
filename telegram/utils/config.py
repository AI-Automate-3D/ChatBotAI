"""Standalone config loader — reads config.json from the project root.

Loads a JSON configuration file and provides access to nested keys.
Can be used independently in any project that follows the same
config.json layout.

Usage
-----
    from telegram.utils.config import load_config

    config = load_config()
    bot_token = config["telegram"]["bot_token"]

    # Or with a custom path:
    config = load_config("/path/to/config.json")
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Default config path: project_root/_config files/config.json
_DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "_config files"
    / "config.json"
)


def load_config(config_path: str | Path | None = None) -> dict:
    """Load and return the full config.json as a dictionary.

    Parameters
    ----------
    config_path : str | Path | None
        Path to the JSON config file.  When *None* the default
        ``<project_root>/_config files/config.json`` is used.

    Returns
    -------
    dict
        Parsed configuration dictionary.

    Raises
    ------
    SystemExit
        If the config file does not exist.
    """
    path = Path(config_path) if config_path else _DEFAULT_CONFIG_PATH

    if not path.exists():
        sys.exit(
            f"ERROR: Config file not found: {path}\n"
            "Copy config.example.json to config.json and fill in your API keys."
        )

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_bot_token(config: dict | None = None, config_path: str | Path | None = None) -> str:
    """Convenience helper — return the Telegram bot token from config.

    Parameters
    ----------
    config : dict | None
        An already-loaded config dict.  If *None*, ``load_config()`` is called.
    config_path : str | Path | None
        Forwarded to ``load_config()`` when *config* is None.

    Returns
    -------
    str
        The bot token string.

    Raises
    ------
    SystemExit
        If the token is missing or empty.
    """
    if config is None:
        config = load_config(config_path)

    token = config.get("telegram", {}).get("bot_token", "")
    if not token:
        sys.exit("ERROR: Missing 'telegram.bot_token' in config.json")
    return token
