"""Send a new email via Gmail.

Standalone function — can be imported and used independently.

Usage
-----
    from gmail.api.send_email import send_email

    result = send_email(
        service,
        to="alice@example.com",
        subject="Hello",
        body="Hi Alice, this is a test.",
    )
"""

from __future__ import annotations

import base64
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from googleapiclient.discovery import Resource

logger = logging.getLogger(__name__)


def _build_mime_message(
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    bcc: str = "",
    from_alias: str = "",
    html: bool = False,
    attachments: list[str | Path] | None = None,
) -> MIMEMultipart | MIMEText:
    """Build a MIME message object.

    Parameters
    ----------
    to : str
        Recipient email address(es), comma-separated.
    subject : str
        Email subject line.
    body : str
        Email body (plain text or HTML).
    cc : str
        CC recipients, comma-separated.
    bcc : str
        BCC recipients, comma-separated.
    from_alias : str
        Sender alias (leave empty for default).
    html : bool
        If *True*, send body as HTML.
    attachments : list[str | Path] | None
        List of file paths to attach.

    Returns
    -------
    MIMEMultipart | MIMEText
        The constructed MIME message.
    """
    if attachments:
        msg = MIMEMultipart()
        msg.attach(MIMEText(body, "html" if html else "plain", "utf-8"))

        for file_path in attachments:
            path = Path(file_path)
            if not path.exists():
                logger.warning("Attachment not found, skipping: %s", path)
                continue

            part = MIMEBase("application", "octet-stream")
            part.set_payload(path.read_bytes())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{path.name}"',
            )
            msg.attach(part)
    else:
        msg = MIMEText(body, "html" if html else "plain", "utf-8")

    msg["To"] = to
    msg["Subject"] = subject
    if cc:
        msg["Cc"] = cc
    if bcc:
        msg["Bcc"] = bcc
    if from_alias:
        msg["From"] = from_alias

    return msg


def send_email(
    service: Resource,
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    bcc: str = "",
    from_alias: str = "",
    html: bool = False,
    attachments: list[str | Path] | None = None,
    user_id: str = "me",
) -> dict:
    """Send a new email via the Gmail API.

    Parameters
    ----------
    service : Resource
        Authenticated Gmail API service object.
    to : str
        Recipient email address(es), comma-separated.
    subject : str
        Email subject line.
    body : str
        Email body (plain text or HTML).
    cc : str
        CC recipients, comma-separated.
    bcc : str
        BCC recipients, comma-separated.
    from_alias : str
        Sender alias (leave empty for default).
    html : bool
        If *True*, send body as HTML.
    attachments : list[str | Path] | None
        List of file paths to attach.
    user_id : str
        Gmail user ID (default ``"me"``).

    Returns
    -------
    dict
        Gmail API send response containing ``id`` and ``threadId``.
    """
    mime_msg = _build_mime_message(
        to=to,
        subject=subject,
        body=body,
        cc=cc,
        bcc=bcc,
        from_alias=from_alias,
        html=html,
        attachments=attachments,
    )

    raw = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode("ascii")
    result = (
        service.users()
        .messages()
        .send(userId=user_id, body={"raw": raw})
        .execute()
    )

    logger.info("Sent email to %s — id=%s", to, result.get("id"))
    return result
