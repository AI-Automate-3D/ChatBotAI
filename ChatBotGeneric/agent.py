"""AI Agent — RAG chatbot that takes a question and returns an answer.

Orchestrates the full pipeline: prompt loading, context retrieval from
Pinecone, chat completion via OpenAI, and conversation memory.

All configuration is read from the local ``config.json`` in this folder.
The system message is loaded from the local ``system_message.txt``.
Memory is stored locally in ``memory.json``.

Usage
-----
    from ChatBotGeneric.agent import run

    answer = run("How do I return an item?")

    # CLI
    python ChatBotGeneric/agent.py "How do I return an item?"
    python ChatBotGeneric/agent.py --clear
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

BOT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BOT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ChatBotGeneric.memory import load_memory, save_memory, clear_memory, append_exchange
from ChatBotGeneric.context import retrieve_context
from ChatBotGeneric.chat import chat
from ChatBotGeneric.prompt import load_prompt

logger = logging.getLogger(__name__)

# Paths — everything lives inside this folder
CONFIG_PATH = BOT_DIR / "config.json"
MEMORY_PATH = BOT_DIR / "memory.json"
SYSTEM_PROMPT_PATH = BOT_DIR / "system_message.txt"


# ── config ───────────────────────────────────────────────────────────────────

def _load_config(config_path: str | Path | None = None) -> dict:
    """Load config.json from the bot folder.

    Parameters
    ----------
    config_path : str | Path | None
        Path to config.json.  Defaults to ``ChatBotGeneric/config.json``.
    """
    path = Path(config_path) if config_path else CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Config file not found: {path}\n"
            "Fill in config.json with your API keys."
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── run ──────────────────────────────────────────────────────────────────────

def run(
    question: str,
    *,
    config_path: str | Path | None = None,
    memory_path: str | Path | None = None,
    system_prompt_override: str | None = None,
) -> str:
    """Ask the agent a question and get a response.

    Parameters
    ----------
    question : str
        The user's question.
    config_path : str | Path | None
        Path to config.json.  Defaults to the local config.
    memory_path : str | Path | None
        Path to the memory JSON file.  Defaults to ``memory.json``.
    system_prompt_override : str | None
        If provided, use this as the system prompt instead of loading
        from system_message.txt.

    Returns
    -------
    str
        The agent's response.
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    question = question.strip()
    mem_path = Path(memory_path) if memory_path else MEMORY_PATH

    # ── load config ─────────────────────────────────────────────────────
    config = _load_config(config_path)

    openai_cfg = config.get("openai", {})
    openai_api_key = openai_cfg.get("api_key", "")
    embedding_model = openai_cfg.get("embedding_model", "text-embedding-3-small")
    chat_model = openai_cfg.get("chat_model", "gpt-4.1")

    if not openai_api_key:
        raise ValueError("Missing 'openai.api_key' in config.json")

    pinecone_cfg = config.get("pinecone", {})
    pinecone_api_key = pinecone_cfg.get("api_key", "")
    index_name = pinecone_cfg.get("index_name", "")
    namespace = pinecone_cfg.get("namespace", "")

    if not pinecone_api_key:
        raise ValueError("Missing 'pinecone.api_key' in config.json")
    if not index_name:
        raise ValueError("Missing 'pinecone.index_name' in config.json")

    agent_cfg = config.get("agent", {})
    top_k = agent_cfg.get("top_k", 5)
    max_history = agent_cfg.get("max_history", 10)

    # ── load system prompt ──────────────────────────────────────────────
    if system_prompt_override:
        system_prompt = system_prompt_override
    else:
        prompt_file = agent_cfg.get("system_prompt_file", "system_message.txt")
        prompt_path = BOT_DIR / prompt_file
        system_prompt = load_prompt(prompt_path)

    # ── load memory ─────────────────────────────────────────────────────
    history = load_memory(mem_path)
    if history:
        pairs = len(history) // 2
        logger.info("Memory: %d previous exchange(s) loaded", pairs)

    # ── retrieve context from Pinecone ──────────────────────────────────
    logger.info("Retrieving context from knowledge base ...")
    context = retrieve_context(
        question=question,
        openai_api_key=openai_api_key,
        pinecone_api_key=pinecone_api_key,
        index_name=index_name,
        namespace=namespace,
        embedding_model=embedding_model,
        top_k=top_k,
    )

    # ── generate response ───────────────────────────────────────────────
    logger.info("Generating response with %s ...", chat_model)
    answer = chat(
        api_key=openai_api_key,
        model=chat_model,
        system_prompt=system_prompt,
        context=context,
        history=history,
        question=question,
    )

    # ── save to memory ──────────────────────────────────────────────────
    history = append_exchange(history, question, answer)
    save_memory(mem_path, history, max_pairs=max_history)

    return answer


# ── CLI entry point ──────────────────────────────────────────────────────────

def main() -> None:
    logging.basicConfig(
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        level=logging.INFO,
    )

    if "--clear" in sys.argv:
        clear_memory(MEMORY_PATH)
        print("Memory cleared.")
        return

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    question = " ".join(args).strip()

    if not question:
        sys.exit(
            "Usage: python ChatBotGeneric/agent.py \"Your question here\"\n"
            "       python ChatBotGeneric/agent.py --clear"
        )

    print(f"Question: {question}")
    answer = run(question)
    print("-" * 50)
    print(answer)


if __name__ == "__main__":
    main()
