"""Reply to an existing email thread via Gmail.

Standalone function — can be imported and used independently.

Usage
-----
    from gmail.api.reply_email import reply_email

    result = reply_email(
        service,
        message_id="18f1a2b3c4d5e6f7",
        thread_id="18f1a2b3c4d5e6f7",
        to="alice@example.com",
        body="Thanks for your message!",
    )
"""

from __future__ import annotations

import base64
import logging
from email.mime.text import MIMEText
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from googleapiclient.discovery import Resource

logger = logging.getLogger(__name__)


def reply_email(
    service: Resource,
    message_id: str,
    thread_id: str,
    to: str,
    body: str,
    subject: str = "",
    cc: str = "",
    html: bool = False,
    user_id: str = "me",
) -> dict:
    """Reply to an existing email message.

    Sends a reply within the same thread.  If ``subject`` is not provided,
    the original subject is fetched and prefixed with ``Re:``.

    Parameters
    ----------
    service : Resource
        Authenticated Gmail API service object.
    message_id : str
        The Gmail message ID to reply to.
    thread_id : str
        The thread ID to keep the reply in the same conversation.
    to : str
        Recipient email address (usually the original sender).
    body : str
        Reply body text (plain text or HTML).
    subject : str
        Subject line for the reply.  If empty, fetches the original
        subject and prepends ``Re:``.
    cc : str
        CC recipients, comma-separated.
    html : bool
        If *True*, send body as HTML.
    user_id : str
        Gmail user ID (default ``"me"``).

    Returns
    -------
    dict
        Gmail API send response containing ``id`` and ``threadId``.
    """
    # Fetch original subject if not provided
    if not subject:
        original = (
            service.users()
            .messages()
            .get(userId=user_id, id=message_id, format="metadata",
                 metadataHeaders=["Subject"])
            .execute()
        )
        headers = original.get("payload", {}).get("headers", [])
        orig_subject = ""
        for h in headers:
            if h.get("name", "").lower() == "subject":
                orig_subject = h.get("value", "")
                break
        subject = orig_subject if orig_subject.lower().startswith("re:") else f"Re: {orig_subject}"

    # Build MIME message
    mime_msg = MIMEText(body, "html" if html else "plain", "utf-8")
    mime_msg["To"] = to
    mime_msg["Subject"] = subject
    mime_msg["In-Reply-To"] = message_id
    mime_msg["References"] = message_id
    if cc:
        mime_msg["Cc"] = cc

    raw = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode("ascii")
    result = (
        service.users()
        .messages()
        .send(
            userId=user_id,
            body={"raw": raw, "threadId": thread_id},
        )
        .execute()
    )

    logger.info("Replied to %s in thread %s — id=%s", message_id, thread_id, result.get("id"))
    return result
