"""Modify email labels — archive, mark read/unread, star, trash, and custom labels.

Standalone functions — can be imported and used independently.

Usage
-----
    from gmail.api.modify_labels import (
        modify_labels, mark_read, mark_unread, archive, trash, star, unstar,
    )

    # Mark as read
    mark_read(service, "18f1a2b3c4d5e6f7")

    # Archive (remove INBOX label)
    archive(service, "18f1a2b3c4d5e6f7")

    # Custom label changes
    modify_labels(service, "18f1a2b3c4d5e6f7",
                  add_labels=["Label_123"], remove_labels=["INBOX"])
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from googleapiclient.discovery import Resource

logger = logging.getLogger(__name__)


def modify_labels(
    service: Resource,
    message_id: str,
    add_labels: list[str] | None = None,
    remove_labels: list[str] | None = None,
    user_id: str = "me",
) -> dict:
    """Add or remove labels from a message.

    Parameters
    ----------
    service : Resource
        Authenticated Gmail API service object.
    message_id : str
        The Gmail message ID.
    add_labels : list[str] | None
        Label IDs to add.
    remove_labels : list[str] | None
        Label IDs to remove.
    user_id : str
        Gmail user ID (default ``"me"``).

    Returns
    -------
    dict
        Updated message resource from the API.
    """
    body: dict = {}
    if add_labels:
        body["addLabelIds"] = add_labels
    if remove_labels:
        body["removeLabelIds"] = remove_labels

    result = (
        service.users()
        .messages()
        .modify(userId=user_id, id=message_id, body=body)
        .execute()
    )
    logger.info(
        "Modified labels on %s: +%s -%s",
        message_id,
        add_labels or [],
        remove_labels or [],
    )
    return result


def batch_modify_labels(
    service: Resource,
    message_ids: list[str],
    add_labels: list[str] | None = None,
    remove_labels: list[str] | None = None,
    user_id: str = "me",
) -> None:
    """Batch-modify labels on multiple messages.

    Parameters
    ----------
    service : Resource
        Authenticated Gmail API service object.
    message_ids : list[str]
        List of Gmail message IDs.
    add_labels : list[str] | None
        Label IDs to add.
    remove_labels : list[str] | None
        Label IDs to remove.
    user_id : str
        Gmail user ID (default ``"me"``).
    """
    body: dict = {"ids": message_ids}
    if add_labels:
        body["addLabelIds"] = add_labels
    if remove_labels:
        body["removeLabelIds"] = remove_labels

    service.users().messages().batchModify(userId=user_id, body=body).execute()
    logger.info(
        "Batch modified %d message(s): +%s -%s",
        len(message_ids),
        add_labels or [],
        remove_labels or [],
    )


# ── convenience helpers ───────────────────────────────────────────────────────


def mark_read(service: Resource, message_id: str, user_id: str = "me") -> dict:
    """Mark a message as read."""
    return modify_labels(service, message_id, remove_labels=["UNREAD"], user_id=user_id)


def mark_unread(service: Resource, message_id: str, user_id: str = "me") -> dict:
    """Mark a message as unread."""
    return modify_labels(service, message_id, add_labels=["UNREAD"], user_id=user_id)


def archive(service: Resource, message_id: str, user_id: str = "me") -> dict:
    """Archive a message (remove from inbox)."""
    return modify_labels(service, message_id, remove_labels=["INBOX"], user_id=user_id)


def unarchive(service: Resource, message_id: str, user_id: str = "me") -> dict:
    """Move a message back to inbox."""
    return modify_labels(service, message_id, add_labels=["INBOX"], user_id=user_id)


def trash(service: Resource, message_id: str, user_id: str = "me") -> dict:
    """Move a message to trash."""
    result = (
        service.users()
        .messages()
        .trash(userId=user_id, id=message_id)
        .execute()
    )
    logger.info("Trashed message %s", message_id)
    return result


def untrash(service: Resource, message_id: str, user_id: str = "me") -> dict:
    """Remove a message from trash."""
    result = (
        service.users()
        .messages()
        .untrash(userId=user_id, id=message_id)
        .execute()
    )
    logger.info("Untrashed message %s", message_id)
    return result


def star(service: Resource, message_id: str, user_id: str = "me") -> dict:
    """Star a message."""
    return modify_labels(service, message_id, add_labels=["STARRED"], user_id=user_id)


def unstar(service: Resource, message_id: str, user_id: str = "me") -> dict:
    """Unstar a message."""
    return modify_labels(service, message_id, remove_labels=["STARRED"], user_id=user_id)


def list_labels(service: Resource, user_id: str = "me") -> list[dict]:
    """List all labels for the authenticated user.

    Returns
    -------
    list[dict]
        Each dict has ``id``, ``name``, ``type``, etc.
    """
    result = service.users().labels().list(userId=user_id).execute()
    labels = result.get("labels", [])
    logger.info("Found %d labels", len(labels))
    return labels
