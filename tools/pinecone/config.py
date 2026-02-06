"""Pinecone configuration.

Self-contained config — reads from environment variables or accepts
explicit values.  No dependency on the rest of the project.

Usage
-----
    from tools.pinecone.config import PineconeConfig

    # From environment variables (.env loaded automatically)
    cfg = PineconeConfig.from_env()

    # Or pass values directly
    cfg = PineconeConfig(
        api_key="pk-...",
        index_name="my-index",
    )
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field


@dataclass
class PineconeConfig:
    """All settings needed to talk to a Pinecone index."""

    api_key: str
    index_name: str
    namespace: str = "default"
    cloud: str = "aws"
    region: str = "us-east-1"

    # --- factory -----------------------------------------------------------

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
