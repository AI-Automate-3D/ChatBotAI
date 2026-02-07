"""Email content parser — extract useful fields from Gmail API message dicts.

Converts the nested Gmail API message format into flat, easy-to-use
dictionaries.  Handles multipart messages, HTML-to-text conversion,
and header extraction.

Designed to be reusable — no pipeline-specific logic.

Usage
-----
    from gmail.utils.parser import parse_message, get_header

    parsed = parse_message(raw_message_dict)
    subject = parsed["subject"]
    body    = parsed["body"]
"""

from __future__ import annotations

import base64
import logging
import re
from email.utils import parsedate_to_datetime

logger = logging.getLogger(__name__)


def get_header(headers: list[dict], name: str) -> str:
    """Extract a single header value by name (case-insensitive).

    Parameters
    ----------
    headers : list[dict]
        The ``payload.headers`` list from a Gmail API message.
    name : str
        Header name to look up (e.g. ``"Subject"``, ``"From"``).

    Returns
    -------
    str
        The header value, or empty string if not found.
    """
    name_lower = name.lower()
    for h in headers:
        if h.get("name", "").lower() == name_lower:
            return h.get("value", "")
    return ""


def _decode_body(data: str) -> str:
    """Decode a base64url-encoded body part to a UTF-8 string."""
    if not data:
        return ""
    try:
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    except Exception as exc:
        logger.warning("Failed to decode body part: %s", exc)
        return ""


def _strip_html(html: str) -> str:
    """Naively strip HTML tags and collapse whitespace.

    For a production system you might want ``beautifulsoup4`` or
    ``html2text``, but this keeps the module dependency-free.
    """
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_body(payload: dict) -> str:
    """Walk the MIME tree and return the best plain-text body."""
    mime_type = payload.get("mimeType", "")

    # Simple single-part message
    if mime_type == "text/plain":
        return _decode_body(payload.get("body", {}).get("data", ""))
    if mime_type == "text/html":
        return _strip_html(_decode_body(payload.get("body", {}).get("data", "")))

    # Multipart — recurse into parts
    parts = payload.get("parts", [])
    plain_text = ""
    html_text = ""

    for part in parts:
        part_mime = part.get("mimeType", "")
        if part_mime == "text/plain":
            plain_text = _decode_body(part.get("body", {}).get("data", ""))
        elif part_mime == "text/html":
            html_text = _decode_body(part.get("body", {}).get("data", ""))
        elif part_mime.startswith("multipart/"):
            # Nested multipart — recurse
            nested = _extract_body(part)
            if nested:
                plain_text = plain_text or nested

    # Prefer plain text over HTML
    if plain_text:
        return plain_text
    if html_text:
        return _strip_html(html_text)
    return ""


def extract_attachments_metadata(payload: dict) -> list[dict]:
    """Return metadata for all attachments in a message payload.

    Parameters
    ----------
    payload : dict
        The ``payload`` field from a Gmail API message.

    Returns
    -------
    list[dict]
        List of ``{"filename", "mime_type", "size", "attachment_id"}`` dicts.
    """
    attachments = []

    def _walk(parts: list[dict]) -> None:
        for part in parts:
            filename = part.get("filename", "")
            body = part.get("body", {})
            if filename and body.get("attachmentId"):
                attachments.append({
                    "filename": filename,
                    "mime_type": part.get("mimeType", ""),
                    "size": body.get("size", 0),
                    "attachment_id": body["attachmentId"],
                })
            if part.get("parts"):
                _walk(part["parts"])

    _walk(payload.get("parts", []))
    return attachments


def parse_message(message: dict) -> dict:
    """Parse a Gmail API message dict into a flat, friendly format.

    Parameters
    ----------
    message : dict
        A full message resource from the Gmail API (format=full).

    Returns
    -------
    dict
        Parsed message with keys: ``id``, ``thread_id``, ``label_ids``,
        ``subject``, ``from``, ``to``, ``cc``, ``date``, ``date_iso``,
        ``snippet``, ``body``, ``attachments``.
    """
    payload = message.get("payload", {})
    headers = payload.get("headers", [])

    date_str = get_header(headers, "Date")
    date_iso = ""
    if date_str:
        try:
            date_iso = parsedate_to_datetime(date_str).isoformat()
        except Exception:
            date_iso = date_str

    return {
        "id": message.get("id", ""),
        "thread_id": message.get("threadId", ""),
        "label_ids": message.get("labelIds", []),
        "subject": get_header(headers, "Subject"),
        "from": get_header(headers, "From"),
        "to": get_header(headers, "To"),
        "cc": get_header(headers, "Cc"),
        "date": date_str,
        "date_iso": date_iso,
        "snippet": message.get("snippet", ""),
        "body": _extract_body(payload),
        "attachments": extract_attachments_metadata(payload),
    }
