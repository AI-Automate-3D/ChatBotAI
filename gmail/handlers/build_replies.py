"""Build reply payloads — reads trigger_queue.json and writes reply_queue.json.

Reads every entry from the Gmail trigger queue, builds a reply payload for
each email, and writes the results to the reply queue.  A separate action
process then picks up the reply queue and sends the replies via Gmail.

Currently echoes the original text back.  Replace ``generate_reply``
with your own logic (e.g. call an AI agent) to customise responses.

Usage
-----
    # Process all pending triggers
    python gmail/handlers/build_replies.py

    # Don't clear the trigger queue after processing
    python gmail/handlers/build_replies.py --no-clear

Data flow
---------
    gmail/triggers/trigger_queue.json  (input)
        -> gmail/handlers/reply_queue.json  (output)
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from gmail.utils.queue_manager import load_queue, save_queue, clear_queue

# ── paths ─────────────────────────────────────────────────────────────────────

HANDLERS_DIR = Path(__file__).resolve().parent              # gmail/handlers/
GMAIL_ROOT = HANDLERS_DIR.parent                             # gmail/
TRIGGER_QUEUE = GMAIL_ROOT / "triggers" / "trigger_queue.json"
REPLY_QUEUE = HANDLERS_DIR / "reply_queue.json"

logger = logging.getLogger(__name__)


# ── reply logic ───────────────────────────────────────────────────────────────

def generate_reply(text: str, subject: str = "") -> str:
    """Generate a reply for the given email text.

    Override this function to plug in your own response logic
    (e.g. an AI agent, lookup table, auto-responder, etc.).

    Parameters
    ----------
    text : str
        The body text of the original email.
    subject : str
        The subject line of the original email.

    Returns
    -------
    str
        The reply text to send back.
    """
    # Default: echo the message back
    return text


def build_replies(
    entries: list[dict],
    filter_from: str | None = None,
) -> list[dict]:
    """Build reply queue entries from trigger queue entries.

    Parameters
    ----------
    entries : list[dict]
        Trigger queue entries (from trigger_queue.json).
    filter_from : str | None
        If set, only process emails from this sender.

    Returns
    -------
    list[dict]
        Reply queue entries ready for the actions stage.
    """
    replies = []

    for entry in entries:
        sender = entry.get("from", "")
        subject = entry.get("subject", "")
        message = entry.get("message", {})
        text = message.get("text", "")

        if not sender or not text:
            logger.warning("Skipping entry — missing sender or text")
            continue

        if filter_from and filter_from.lower() not in sender.lower():
            continue

        reply_entry = {
            "id": entry.get("id"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "gmail_message_id": entry.get("gmail_message_id"),
            "gmail_thread_id": entry.get("gmail_thread_id"),
            "to": sender,
            "subject": subject,
            "original_message": message,
            "reply": {
                "text": generate_reply(text, subject),
            },
        }
        replies.append(reply_entry)

    return replies


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    logging.basicConfig(
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        level=logging.INFO,
    )

    parser = argparse.ArgumentParser(
        description="Read trigger_queue.json and write reply_queue.json.",
    )
    parser.add_argument(
        "--from", "-f",
        dest="filter_from",
        default=None,
        help="Only process emails from this sender (default: all)",
    )
    parser.add_argument(
        "--no-clear",
        action="store_true",
        default=False,
        help="Don't clear trigger_queue.json after processing",
    )
    args = parser.parse_args()

    # Load trigger queue
    entries = load_queue(TRIGGER_QUEUE)
    if not entries:
        print("No pending messages in trigger_queue.json")
        return

    print(f"Found {len(entries)} message(s) in trigger_queue.json")

    # Build replies
    replies = build_replies(entries, filter_from=args.filter_from)
    print(f"Built {len(replies)} reply(s)")

    # Write reply queue
    save_queue(REPLY_QUEUE, replies)
    print(f"Output written to {REPLY_QUEUE}")

    # Clear trigger queue
    if not args.no_clear:
        clear_queue(TRIGGER_QUEUE)
        logger.info("Cleared trigger_queue.json")


if __name__ == "__main__":
    main()
