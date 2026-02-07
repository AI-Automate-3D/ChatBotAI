"""Download email attachments from Gmail.

Standalone function — can be imported and used independently.

Usage
-----
    from gmail.api.get_attachments import (
        get_attachment, download_all_attachments,
    )

    # Download a single attachment by ID
    data = get_attachment(service, "msg_id", "attachment_id")

    # Download all attachments from a message to a folder
    files = download_all_attachments(service, "msg_id", output_dir="downloads/")
"""

from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from googleapiclient.discovery import Resource

from gmail.utils.parser import extract_attachments_metadata

logger = logging.getLogger(__name__)


def get_attachment(
    service: Resource,
    message_id: str,
    attachment_id: str,
    user_id: str = "me",
) -> bytes:
    """Download a single attachment by its ID.

    Parameters
    ----------
    service : Resource
        Authenticated Gmail API service object.
    message_id : str
        The Gmail message ID containing the attachment.
    attachment_id : str
        The attachment ID (from ``body.attachmentId``).
    user_id : str
        Gmail user ID (default ``"me"``).

    Returns
    -------
    bytes
        The raw attachment data.
    """
    result = (
        service.users()
        .messages()
        .attachments()
        .get(userId=user_id, messageId=message_id, id=attachment_id)
        .execute()
    )

    data = base64.urlsafe_b64decode(result["data"])
    logger.info(
        "Downloaded attachment %s from message %s (%d bytes)",
        attachment_id, message_id, len(data),
    )
    return data


def download_all_attachments(
    service: Resource,
    message_id: str,
    output_dir: str | Path = "downloads",
    user_id: str = "me",
) -> list[Path]:
    """Download all attachments from a message to a local directory.

    Parameters
    ----------
    service : Resource
        Authenticated Gmail API service object.
    message_id : str
        The Gmail message ID.
    output_dir : str | Path
        Directory to save attachments into (created if needed).
    user_id : str
        Gmail user ID (default ``"me"``).

    Returns
    -------
    list[Path]
        List of paths to downloaded files.
    """
    # Fetch the full message to get attachment metadata
    message = (
        service.users()
        .messages()
        .get(userId=user_id, id=message_id, format="full")
        .execute()
    )

    attachments_meta = extract_attachments_metadata(message.get("payload", {}))
    if not attachments_meta:
        logger.info("No attachments in message %s", message_id)
        return []

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    saved_files: list[Path] = []
    for att in attachments_meta:
        data = get_attachment(service, message_id, att["attachment_id"], user_id)
        file_path = out / att["filename"]

        # Avoid overwriting — append a counter if needed
        if file_path.exists():
            stem = file_path.stem
            suffix = file_path.suffix
            counter = 1
            while file_path.exists():
                file_path = out / f"{stem}_{counter}{suffix}"
                counter += 1

        file_path.write_bytes(data)
        saved_files.append(file_path)
        logger.info("Saved attachment: %s (%d bytes)", file_path, len(data))

    return saved_files
