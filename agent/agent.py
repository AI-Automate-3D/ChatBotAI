"""AI Agent — RAG chatbot that takes a question and returns an answer.

Orchestrates the full RAG (Retrieval-Augmented Generation) pipeline:
prompt loading, context retrieval, chat completion, and memory management.

Each step uses a standalone module that can be imported independently:
    - ``agent.prompt``  — system prompt loading
    - ``agent.context`` — vector store context retrieval
    - ``agent.chat``    — OpenAI chat completion
    - ``agent.memory``  — conversation history

Usage
-----
    from agent.agent import run

    # Direct function call — returns the answer as a string
    answer = run("How do I return an item?")
    print(answer)

    # CLI usage (question passed as argument)
    python agent/agent.py "How do I return an item?"

    # Clear memory
    python agent/agent.py --clear
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

# Ensure project root is on the Python path so `tools` is importable
AGENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = AGENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent.memory import load_memory, save_memory, clear_memory, append_exchange
from agent.context import retrieve_context
from agent.chat import chat
from agent.prompt import load_prompt

logger = logging.getLogger(__name__)

# Paths
CONFIG_PATH = PROJECT_ROOT / "_config files" / "config.json"
MEMORY_PATH = AGENT_DIR / "memory.json"


# ── config ───────────────────────────────────────────────────────────────────

def _load_config(config_path: str | Path | None = None) -> dict:
    """Load the full config.json from the project root.

    Parameters
    ----------
    config_path : str | Path | None
        Path to config.json.  Defaults to ``<project_root>/_config files/config.json``.
    """
    path = Path(config_path) if config_path else CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Config file not found: {path}\n"
            "Copy config.example.json to config.json and fill in your API keys."
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

    This is the primary entry point.  Pass a question string directly
    and receive the answer as a return value — no file I/O required.

    Parameters
    ----------
    question : str
        The user's question.
    config_path : str | Path | None
        Path to config.json.  Defaults to the project-level config.
    memory_path : str | Path | None
        Path to the memory JSON file.  Defaults to ``agent/memory.json``.
    system_prompt_override : str | None
        If provided, use this as the system prompt instead of loading
        from the config / prompt file.

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

    if not openai_api_key:
        raise ValueError("Missing 'openai.api_key' in config.json")

    agent_cfg = config.get("agent", {})
    chat_model = agent_cfg.get("chat_model", "gpt-4.1")
    top_k = agent_cfg.get("top_k", 5)
    max_history = agent_cfg.get("max_history", 10)

    # ── load system prompt ──────────────────────────────────────────────
    if system_prompt_override:
        system_prompt = system_prompt_override
    else:
        prompt_file = agent_cfg.get("system_prompt_file", "")
        prompt_path = PROJECT_ROOT / prompt_file if prompt_file else None
        system_prompt = load_prompt(
            prompt_path,
            default=agent_cfg.get("system_prompt"),
        )

    # ── load memory ─────────────────────────────────────────────────────
    history = load_memory(mem_path)
    if history:
        pairs = len(history) // 2
        logger.info("Memory: %d previous exchange(s) loaded", pairs)

    # ── retrieve context from Pinecone ──────────────────────────────────
    logger.info("Retrieving context from knowledge base ...")
    cfg_path = Path(config_path) if config_path else CONFIG_PATH
    context = retrieve_context(
        question=question,
        openai_api_key=openai_api_key,
        embedding_model=embedding_model,
        config_path=cfg_path,
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

    # Handle --clear flag
    if "--clear" in sys.argv:
        clear_memory(MEMORY_PATH)
        print("Memory cleared.")
        return

    # Get question from CLI arguments (everything that isn't a flag)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    question = " ".join(args).strip()

    if not question:
        sys.exit(
            "Usage: python agent/agent.py \"Your question here\"\n"
            "       python agent/agent.py --clear"
        )

    print(f"Question: {question}")

    answer = run(question)

    print("-" * 50)
    print(answer)


if __name__ == "__main__":
    main()
