"""Pinecone configuration.

Self-contained config — reads from a JSON file, environment variables,
or accepts explicit values.  No dependency on the rest of the project.

Usage
-----
    from tools.pinecone.config import PineconeConfig

    # From a JSON config file (recommended)
    cfg = PineconeConfig.from_json("config.json")

    # From environment variables (.env loaded automatically)
    cfg = PineconeConfig.from_env()

    # Or pass values directly
    cfg = PineconeConfig(
        api_key="pk-...",
        index_name="my-index",
    )
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass


@dataclass
class PineconeConfig:
    """All settings needed to talk to a Pinecone index."""

    api_key: str
    index_name: str
    namespace: str = "default"
    cloud: str = "aws"
    region: str = "us-east-1"

    # --- factories ---------------------------------------------------------

    @classmethod
    def from_json(cls, json_file: str) -> PineconeConfig:
        """Build config from a JSON file.

        Expected structure::

            {
              "pinecone": {
                "api_key": "...",
                "index_name": "...",
                "namespace": "chatbot",
                "cloud": "aws",
                "region": "us-east-1"
              }
            }

        The ``pinecone`` key is required.  ``api_key`` and ``index_name``
        are required; the rest have sensible defaults.
        """
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            sys.exit(f"ERROR: Config file not found: {json_file}")
        except json.JSONDecodeError as exc:
            sys.exit(f"ERROR: Invalid JSON in {json_file}: {exc}")

        pc = data.get("pinecone", {})

        api_key = pc.get("api_key", "")
        index_name = pc.get("index_name", "")

        if not api_key:
            sys.exit(f"ERROR: Missing 'pinecone.api_key' in {json_file}")
        if not index_name:
            sys.exit(f"ERROR: Missing 'pinecone.index_name' in {json_file}")

        return cls(
            api_key=api_key,
            index_name=index_name,
            namespace=pc.get("namespace", "default"),
            cloud=pc.get("cloud", "aws"),
            region=pc.get("region", "us-east-1"),
        )

    @classmethod
    def from_env(cls, env_file: str | None = None) -> PineconeConfig:
        """Build config from environment variables.

        If *env_file* is given, it is loaded first (requires python-dotenv).
        Otherwise only ``os.environ`` is consulted.

        Required env vars:
            PINECONE_API_KEY
            PINECONE_INDEX_NAME

        Optional env vars (with defaults):
            PINECONE_NAMESPACE   ("default")
            PINECONE_CLOUD       ("aws")
            PINECONE_REGION      ("us-east-1")
        """
        if env_file:
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file)
            except ImportError:
                sys.exit(
                    "python-dotenv is required to load an env file. "
                    "Install it with: pip install python-dotenv"
                )

        api_key = os.getenv("PINECONE_API_KEY", "")
        index_name = os.getenv("PINECONE_INDEX_NAME", "")

        if not api_key:
            sys.exit("ERROR: Missing required env var PINECONE_API_KEY")
        if not index_name:
            sys.exit("ERROR: Missing required env var PINECONE_INDEX_NAME")

        return cls(
            api_key=api_key,
            index_name=index_name,
            namespace=os.getenv("PINECONE_NAMESPACE", "default"),
            cloud=os.getenv("PINECONE_CLOUD", "aws"),
            region=os.getenv("PINECONE_REGION", "us-east-1"),
        )
