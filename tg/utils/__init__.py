"""Shared standalone utilities — config, logging, queue management.

Each module can be imported and used independently:

    from tg.utils.config import load_config, get_bot_token
    from tg.utils.chat_logger import log_update
    from tg.utils.queue_manager import load_queue, append_queue, clear_queue
"""

from tg.utils.config import load_config, get_bot_token
from tg.utils.chat_logger import log_update, build_log_entry
from tg.utils.queue_manager import load_queue, save_queue, append_queue, clear_queue

__all__ = [
    "load_config",
    "get_bot_token",
    "log_update",
    "build_log_entry",
    "load_queue",
    "save_queue",
    "append_queue",
    "clear_queue",
]
