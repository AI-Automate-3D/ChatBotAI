"""Pinecone client factory.

Thin wrapper so every module doesn't create its own ``Pinecone()`` instance.

Usage
-----
    from tools.pinecone.config  import PineconeConfig
    from tools.pinecone.client  import get_client, get_index

    cfg   = PineconeConfig.from_env()
    pc    = get_client(cfg)
    index = get_index(cfg)
"""

from __future__ import annotations

from pinecone import Pinecone

from tools.pinecone.config import PineconeConfig


def get_client(config: PineconeConfig) -> Pinecone:
    """Return an authenticated Pinecone client."""
    return Pinecone(api_key=config.api_key)


def get_index(config: PineconeConfig):
    """Return a ready-to-use Pinecone Index object."""
    pc = get_client(config)
    return pc.Index(config.index_name)
