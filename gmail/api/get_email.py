"""Fetch a single email by ID from Gmail.

Standalone function — can be imported and used independently.

Usage
-----
    from gmail.api.get_email import get_email

    # Returns parsed dict
    email = get_email(service, "18f1a2b3c4d5e6f7")

    # Returns raw Gmail API response
    raw = get_email(service, "18f1a2b3c4d5e6f7", parse=False)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from googleapiclient.discovery import Resource

from gmail.utils.parser import parse_message

logger = logging.getLogger(__name__)


def get_email(
    service: Resource,
    message_id: str,
    user_id: str = "me",
    parse: bool = True,
    fmt: str = "full",
) -> dict:
    """Fetch a single email message by ID.

    Parameters
    ----------
    service : Resource
        Authenticated Gmail API service object.
    message_id : str
        The Gmail message ID.
    user_id : str
        Gmail user ID (default ``"me"`` = authenticated user).
    parse : bool
        If *True*, return a parsed dict via ``parser.parse_message()``.
        If *False*, return the raw Gmail API response.
    fmt : str
        Gmail API format parameter: ``"full"``, ``"metadata"``,
        ``"minimal"``, or ``"raw"``.

    Returns
    -------
    dict
        Parsed email dict or raw API response.
    """
    message = (
        service.users()
        .messages()
        .get(userId=user_id, id=message_id, format=fmt)
        .execute()
    )
    logger.info("Fetched email %s", message_id)

    if parse and fmt == "full":
        return parse_message(message)
    return message
