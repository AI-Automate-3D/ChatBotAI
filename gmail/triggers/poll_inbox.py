"""Poll Gmail inbox for new unread emails and queue them for processing.

Checks for unread messages in the inbox, writes new ones to the trigger
queue, and optionally marks them as read so they aren't re-processed.

Usage
-----
    # Poll once
    python gmail/triggers/poll_inbox.py

    # Poll only unread messages matching a query
    python gmail/triggers/poll_inbox.py --query "from:alice"

    # Don't mark messages as read after queuing
    python gmail/triggers/poll_inbox.py --no-mark-read

    # Limit to N messages per poll
    python gmail/triggers/poll_inbox.py --max 5

Data flow
---------
    Gmail Inbox (unread)
        -> gmail/triggers/trigger_queue.json
        -> messages marked as read (optional)
"""

from __future__ import annotations

import argparse
import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from gmail.utils.auth import get_gmail_service
from gmail.utils.parser import parse_message
from gmail.utils.queue_manager import append_queue
from gmail.api.modify_labels import mark_read

# ── paths ─────────────────────────────────────────────────────────────────────

TRIGGERS_DIR = Path(__file__).resolve().parent           # gmail/triggers/
TRIGGER_QUEUE = TRIGGERS_DIR / "trigger_queue.json"

logger = logging.getLogger(__name__)


# ── poll ──────────────────────────────────────────────────────────────────────

def poll_inbox(
    service,
    query: str = "",
    max_results: int = 20,
    mark_as_read: bool = True,
    user_id: str = "me",
) -> int:
    """Poll for unread inbox messages and append them to the trigger queue.

    Parameters
    ----------
    service
        Authenticated Gmail API service object.
    query : str
        Additional Gmail search query to narrow results.
    max_results : int
        Maximum number of messages to fetch per poll.
    mark_as_read : bool
        If *True*, mark each queued message as read.
    user_id : str
        Gmail user ID (default ``"me"``).

    Returns
    -------
    int
        Number of messages queued.
    """
    # Build query: always unread + inbox, plus any user filter
    full_query = "is:unread in:inbox"
    if query:
        full_query += f" {query}"

    # List matching message IDs
    response = (
        service.users()
        .messages()
        .list(userId=user_id, q=full_query, maxResults=max_results)
        .execute()
    )
    messages_meta = response.get("messages", [])

    if not messages_meta:
        logger.info("No new unread messages")
        return 0

    logger.info("Found %d unread message(s)", len(messages_meta))
    queued = 0

    for meta in messages_meta:
        msg_id = meta["id"]

        # Fetch full message
        raw_msg = (
            service.users()
            .messages()
            .get(userId=user_id, id=msg_id, format="full")
            .execute()
        )
        parsed = parse_message(raw_msg)

        # Build trigger entry
        entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "gmail",
            "gmail_message_id": parsed["id"],
            "gmail_thread_id": parsed["thread_id"],
            "from": parsed["from"],
            "to": parsed["to"],
            "subject": parsed["subject"],
            "date": parsed["date_iso"],
            "message": {
                "text": parsed["body"],
                "snippet": parsed["snippet"],
                "has_attachments": len(parsed["attachments"]) > 0,
            },
        }

        append_queue(TRIGGER_QUEUE, entry)
        queued += 1

        # Mark as read so we don't re-process
        if mark_as_read:
            mark_read(service, msg_id, user_id=user_id)

    logger.info("Queued %d message(s) to %s", queued, TRIGGER_QUEUE)
    return queued


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    logging.basicConfig(
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        level=logging.INFO,
    )

    parser = argparse.ArgumentParser(
        description="Poll Gmail inbox for new unread messages.",
    )
    parser.add_argument(
        "--query", "-q",
        default="",
        help="Additional Gmail search query (e.g. 'from:alice')",
    )
    parser.add_argument(
        "--max", "-m",
        type=int,
        default=20,
        dest="max_results",
        help="Max messages to fetch per poll (default: 20)",
    )
    parser.add_argument(
        "--no-mark-read",
        action="store_true",
        default=False,
        help="Don't mark messages as read after queuing",
    )
    args = parser.parse_args()

    service = get_gmail_service()
    queued = poll_inbox(
        service,
        query=args.query,
        max_results=args.max_results,
        mark_as_read=not args.no_mark_read,
    )
    print(f"Queued {queued} new message(s)")


if __name__ == "__main__":
    main()
