"""Send replies — reads reply_queue.json and sends each reply via Gmail.

Reads the reply queue produced by ``handlers/build_replies.py`` and
sends each reply to the original sender using the Gmail API.

Usage
-----
    # Send all pending replies
    python gmail/actions/send_replies.py

    # Don't clear the reply queue after sending
    python gmail/actions/send_replies.py --no-clear

Data flow
---------
    gmail/handlers/reply_queue.json  (input)
        -> Gmail API  (sends replies)
        -> reply_queue.json cleared
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from gmail.utils.auth import get_gmail_service
from gmail.utils.queue_manager import load_queue, clear_queue
from gmail.api.reply_email import reply_email
from gmail.api.send_email import send_email

# ── paths ─────────────────────────────────────────────────────────────────────

ACTIONS_DIR = Path(__file__).resolve().parent               # gmail/actions/
GMAIL_ROOT = ACTIONS_DIR.parent                              # gmail/
REPLY_QUEUE = GMAIL_ROOT / "handlers" / "reply_queue.json"

logger = logging.getLogger(__name__)


# ── send ──────────────────────────────────────────────────────────────────────

def send_all(
    service,
    entries: list[dict],
) -> int:
    """Send each reply entry via Gmail.

    If the entry has ``gmail_message_id`` and ``gmail_thread_id``, sends
    as a threaded reply.  Otherwise sends as a new email.

    Parameters
    ----------
    service
        Authenticated Gmail API service object.
    entries : list[dict]
        Reply queue entries (from reply_queue.json).

    Returns
    -------
    int
        Number of messages successfully sent.
    """
    sent = 0

    for entry in entries:
        to = entry.get("to", "")
        subject = entry.get("subject", "")
        text = entry.get("reply", {}).get("text", "")
        msg_id = entry.get("gmail_message_id")
        thread_id = entry.get("gmail_thread_id")

        if not to or not text:
            logger.warning("Skipping entry — missing recipient or reply text")
            continue

        try:
            if msg_id and thread_id:
                reply_email(
                    service,
                    message_id=msg_id,
                    thread_id=thread_id,
                    to=to,
                    body=text,
                    subject=subject,
                )
            else:
                send_email(
                    service,
                    to=to,
                    subject=subject or "(no subject)",
                    body=text,
                )
            logger.info("Sent reply to %s: %s", to, text[:80])
            sent += 1
        except Exception as exc:
            logger.error("Failed to send to %s: %s", to, exc)

    return sent


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    logging.basicConfig(
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        level=logging.INFO,
    )

    parser = argparse.ArgumentParser(
        description="Read reply_queue.json and send replies via Gmail.",
    )
    parser.add_argument(
        "--no-clear",
        action="store_true",
        default=False,
        help="Don't clear reply_queue.json after sending",
    )
    args = parser.parse_args()

    # Authenticate
    service = get_gmail_service()

    # Load reply queue
    entries = load_queue(REPLY_QUEUE)
    if not entries:
        print("No pending replies in reply_queue.json")
        return

    print(f"Found {len(entries)} reply(s) in reply_queue.json")

    # Send
    sent = send_all(service, entries)
    print(f"Sent {sent} message(s)")

    # Clear
    if not args.no_clear:
        clear_queue(REPLY_QUEUE)
        logger.info("Cleared reply_queue.json")


if __name__ == "__main__":
    main()
