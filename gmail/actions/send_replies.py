"""Send replies via Gmail — takes reply entries directly.

Sends each reply entry to the original sender using the Gmail API.
Accepts reply entries as function arguments — no file I/O.

Usage
-----
    from gmail.actions.send_replies import send_all

    # Send a list of reply entries
    sent_count = send_all(service, entries)

    # CLI usage
    python gmail/actions/send_replies.py --replies '[{"to":"a@b.com","reply":{"text":"Hi"}}]'
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from gmail.utils.auth import get_gmail_service
from gmail.api.reply_email import reply_email
from gmail.api.send_email import send_email

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
        Reply entries — each should have ``to``, ``reply.text``, and
        optionally ``gmail_message_id`` / ``gmail_thread_id``.

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
        description="Send reply entries via Gmail API.",
    )
    parser.add_argument(
        "--replies", "-r",
        type=str,
        default=None,
        help="JSON string of reply entries (list of dicts)",
    )
    args = parser.parse_args()

    if not args.replies:
        print(
            "Usage:\n"
            '  python gmail/actions/send_replies.py --replies \'[{"to":"a@b.com","reply":{"text":"Hi"}}]\''
        )
        return

    service = get_gmail_service()
    entries = json.loads(args.replies)
    print(f"Sending {len(entries)} reply(s) ...")

    sent = send_all(service, entries)
    print(f"Sent {sent} message(s)")


if __name__ == "__main__":
    main()
