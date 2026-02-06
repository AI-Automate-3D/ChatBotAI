"""Build output messages — reads telegram_input.json and writes telegram_output.json.

Reads every entry from the input JSON, echoes the exact text back with
the chat info, and writes the result to telegram_output.json in the
output folder. A separate process can then read the output file and
send the messages via Telegram.

Usage
-----
    # Process all pending messages
    python telegram/output/send_message.py

    # Process only messages from a specific chat
    python telegram/output/send_message.py --chat-id 123456789

    # Don't clear the input after processing
    python telegram/output/send_message.py --no-clear
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── paths ────────────────────────────────────────────────────────────────────

OUTPUT_DIR = Path(__file__).resolve().parent         # telegram/output/
TELEGRAM_ROOT = OUTPUT_DIR.parent                     # telegram/
PROJECT_ROOT = TELEGRAM_ROOT.parent                   # project root
INPUT_PATH = TELEGRAM_ROOT / "input" / "telegram_input.json"
OUTPUT_PATH = OUTPUT_DIR / "telegram_output.json"

logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ── helpers ──────────────────────────────────────────────────────────────────

def load_input() -> list[dict]:
    """Load pending messages from telegram_input.json."""
    if not INPUT_PATH.exists():
        return []
    data = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def clear_input() -> None:
    """Reset telegram_input.json to an empty array."""
    INPUT_PATH.write_text("[]", encoding="utf-8")


def write_output(entries: list[dict]) -> None:
    """Write output entries to telegram_output.json."""
    OUTPUT_PATH.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


# ── build output ─────────────────────────────────────────────────────────────

def build_output(entries: list[dict], filter_chat_id: int | None = None) -> list[dict]:
    """Build output entries — echo the exact text back with chat info."""
    output = []

    for entry in entries:
        chat = entry.get("chat", {})
        chat_id = chat.get("id")
        user = entry.get("user", {})
        message = entry.get("message", {})
        text = message.get("text")

        if not chat_id or not text:
            logger.warning("Skipping entry — missing chat id or text")
            continue

        if filter_chat_id and chat_id != filter_chat_id:
            continue

        output_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "chat": chat,
            "user": user,
            "original_message": message,
            "reply": {
                "text": text,
            },
        }
        output.append(output_entry)

    return output


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read telegram_input.json and write telegram_output.json.",
    )
    parser.add_argument(
        "--chat-id", "-c",
        type=int,
        default=None,
        help="Only process messages from this chat ID (default: all chats)",
    )
    parser.add_argument(
        "--no-clear",
        action="store_true",
        default=False,
        help="Don't clear telegram_input.json after processing",
    )
    args = parser.parse_args()

    # Load input
    entries = load_input()
    if not entries:
        print("No pending messages in telegram_input.json")
        return

    print(f"Found {len(entries)} message(s) in telegram_input.json")

    # Build output
    output = build_output(entries, filter_chat_id=args.chat_id)
    print(f"Built {len(output)} reply(s)")

    # Write output
    write_output(output)
    logger.info("Written to %s", OUTPUT_PATH)
    print(f"Output written to {OUTPUT_PATH}")

    # Clear input
    if not args.no_clear:
        clear_input()
        logger.info("Cleared telegram_input.json")


if __name__ == "__main__":
    main()
