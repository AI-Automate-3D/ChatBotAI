"""Build reply payloads from Gmail trigger entries.

Takes a list of trigger entries (incoming emails) and builds a reply
payload for each one.  Returns the replies directly — no file I/O.

The ``generate_reply`` function is a pluggable hook.  Replace it with
your own logic (e.g. call an AI agent) to customise responses.

Usage
-----
    from gmail.handlers.build_replies import build_replies, run

    # Direct function call with a list of trigger entries
    replies = build_replies(entries)

    # Or use run() for a single email text
    reply_text = run("Thanks for your email!", subject="Re: Hello")

    # CLI usage
    python gmail/handlers/build_replies.py --message "Hello!"
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

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


def run(text: str, subject: str = "") -> str:
    """Generate a reply for a single email body.

    Convenience wrapper that calls ``generate_reply`` directly.

    Parameters
    ----------
    text : str
        The email body text.
    subject : str
        The email subject line.

    Returns
    -------
    str
        The reply text.
    """
    return generate_reply(text, subject)


def build_replies(
    entries: list[dict],
    filter_from: str | None = None,
) -> list[dict]:
    """Build reply queue entries from trigger queue entries.

    Parameters
    ----------
    entries : list[dict]
        Trigger entries — each should have ``from``, ``subject``, and
        ``message`` keys.
    filter_from : str | None
        If set, only process emails from this sender.

    Returns
    -------
    list[dict]
        Reply entries ready for sending.
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
        description="Build reply payloads from Gmail trigger entries.",
    )
    parser.add_argument(
        "--trigger", "-t",
        type=str,
        default=None,
        help="JSON string of trigger entries (list of dicts)",
    )
    parser.add_argument(
        "--message", "-m",
        type=str,
        default=None,
        help="Single email body text to generate a reply for",
    )
    parser.add_argument(
        "--subject", "-s",
        type=str,
        default="",
        help="Email subject line (used with --message)",
    )
    parser.add_argument(
        "--from", "-f",
        dest="filter_from",
        default=None,
        help="Only process emails from this sender",
    )
    args = parser.parse_args()

    if args.message:
        reply = run(args.message, subject=args.subject)
        print(f"Reply: {reply}")
        return

    if args.trigger:
        entries = json.loads(args.trigger)
        replies = build_replies(entries, filter_from=args.filter_from)
        print(json.dumps(replies, indent=2, default=str))
        return

    print(
        "Usage:\n"
        '  python gmail/handlers/build_replies.py --message "Hello!"\n'
        '  python gmail/handlers/build_replies.py --trigger \'[{"from":"a@b.com",...}]\''
    )


if __name__ == "__main__":
    main()
