"""Search and list emails from Gmail.

Standalone function — can be imported and used independently.

Usage
-----
    from gmail.api.list_emails import list_emails, search_emails

    # List recent inbox messages
    emails = list_emails(service, label_ids=["INBOX"], max_results=10)

    # Search with Gmail query syntax
    emails = search_emails(service, query="from:alice subject:meeting")
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from googleapiclient.discovery import Resource

from gmail.utils.parser import parse_message

logger = logging.getLogger(__name__)


def list_emails(
    service: Resource,
    user_id: str = "me",
    label_ids: list[str] | None = None,
    query: str = "",
    max_results: int = 20,
    parse: bool = True,
    page_token: str | None = None,
) -> dict:
    """List emails matching the given criteria.

    Parameters
    ----------
    service : Resource
        Authenticated Gmail API service object.
    user_id : str
        Gmail user ID (default ``"me"``).
    label_ids : list[str] | None
        Filter by label IDs (e.g. ``["INBOX"]``, ``["UNREAD"]``).
    query : str
        Gmail search query (same syntax as the Gmail search bar).
    max_results : int
        Maximum number of messages to return.
    parse : bool
        If *True*, fetch full message details and parse each one.
        If *False*, return only message IDs and thread IDs.
    page_token : str | None
        Token for fetching the next page of results.

    Returns
    -------
    dict
        ``{"messages": [...], "next_page_token": str | None,
        "result_size_estimate": int}``.
    """
    kwargs: dict = {
        "userId": user_id,
        "maxResults": max_results,
    }
    if label_ids:
        kwargs["labelIds"] = label_ids
    if query:
        kwargs["q"] = query
    if page_token:
        kwargs["pageToken"] = page_token

    response = service.users().messages().list(**kwargs).execute()

    messages_meta = response.get("messages", [])
    next_token = response.get("nextPageToken")
    estimate = response.get("resultSizeEstimate", 0)

    logger.info(
        "Listed %d message(s) (estimate: %d, query: %r)",
        len(messages_meta), estimate, query or "(none)",
    )

    if not parse:
        return {
            "messages": messages_meta,
            "next_page_token": next_token,
            "result_size_estimate": estimate,
        }

    # Fetch and parse each message
    parsed = []
    for meta in messages_meta:
        msg = (
            service.users()
            .messages()
            .get(userId=user_id, id=meta["id"], format="full")
            .execute()
        )
        parsed.append(parse_message(msg))

    return {
        "messages": parsed,
        "next_page_token": next_token,
        "result_size_estimate": estimate,
    }


def search_emails(
    service: Resource,
    query: str,
    user_id: str = "me",
    max_results: int = 20,
    parse: bool = True,
) -> list[dict]:
    """Search Gmail and return matching messages.

    Convenience wrapper around ``list_emails`` that returns only the
    messages list (no pagination metadata).

    Parameters
    ----------
    service : Resource
        Authenticated Gmail API service object.
    query : str
        Gmail search query.
    user_id : str
        Gmail user ID (default ``"me"``).
    max_results : int
        Maximum number of results.
    parse : bool
        If *True*, return parsed dicts.

    Returns
    -------
    list[dict]
        List of parsed email dicts or raw metadata.
    """
    result = list_emails(
        service,
        user_id=user_id,
        query=query,
        max_results=max_results,
        parse=parse,
    )
    return result["messages"]
