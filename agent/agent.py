"""AI Agent — reads input.txt, queries the knowledge base, writes output.txt.

Orchestrates the full RAG (Retrieval-Augmented Generation) pipeline:
prompt loading, context retrieval, chat completion, and memory management.

Each step uses a standalone module that can be imported independently:
    - ``agent.prompt``  — system prompt loading
    - ``agent.context`` — vector store context retrieval
    - ``agent.chat``    — OpenAI chat completion
    - ``agent.memory``  — conversation history

Usage
-----
    # Write a question
    echo "How do I return an item?" > agent/input.txt

    # Run the agent
    python agent/agent.py

    # Read the answer
    cat agent/output.txt

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

logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Paths
CONFIG_PATH = PROJECT_ROOT / "_config files" / "config.json"
INPUT_PATH = AGENT_DIR / "input.txt"
OUTPUT_PATH = AGENT_DIR / "output.txt"
MEMORY_PATH = AGENT_DIR / "memory.json"


# ── config ──────────────────────────────────────────────────────────────────

def load_config() -> dict:
    """Load the full config.json from the project root."""
    if not CONFIG_PATH.exists():
        sys.exit(
            f"ERROR: Config file not found: {CONFIG_PATH}\n"
            "Copy config.example.json to config.json and fill in your API keys."
        )
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ── main ────────────────────────────────────────────────────────────────────

def main() -> None:
    # Handle --clear flag
    if "--clear" in sys.argv:
        clear_memory(MEMORY_PATH)
        print("Memory cleared.")
        return

    # ── load config ────────────────────────────────────────────────────────
    config = load_config()

    openai_cfg = config.get("openai", {})
    openai_api_key = openai_cfg.get("api_key", "")
    embedding_model = openai_cfg.get("embedding_model", "text-embedding-3-small")

    if not openai_api_key:
        sys.exit("ERROR: Missing 'openai.api_key' in config.json")

    agent_cfg = config.get("agent", {})
    chat_model = agent_cfg.get("chat_model", "gpt-4.1")
    top_k = agent_cfg.get("top_k", 5)
    max_history = agent_cfg.get("max_history", 10)

    # ── load system prompt ─────────────────────────────────────────────────
    prompt_file = agent_cfg.get("system_prompt_file", "")
    if prompt_file:
        prompt_path = PROJECT_ROOT / prompt_file
    else:
        prompt_path = None

    system_prompt = load_prompt(
        prompt_path,
        default=agent_cfg.get("system_prompt"),
    )

    # ── read input ─────────────────────────────────────────────────────────
    if not INPUT_PATH.exists():
        sys.exit(f"ERROR: No input file found at {INPUT_PATH}")

    question = INPUT_PATH.read_text(encoding="utf-8").strip()
    if not question:
        sys.exit("ERROR: input.txt is empty.")

    print(f"Question: {question}")

    # ── load memory ────────────────────────────────────────────────────────
    history = load_memory(MEMORY_PATH)
    if history:
        pairs = len(history) // 2
        print(f"Memory: {pairs} previous exchange(s) loaded")

    # ── retrieve context from Pinecone ─────────────────────────────────────
    print("Retrieving context from knowledge base ...")
    context = retrieve_context(
        question=question,
        openai_api_key=openai_api_key,
        embedding_model=embedding_model,
        config_path=CONFIG_PATH,
        top_k=top_k,
    )

    # ── generate response ──────────────────────────────────────────────────
    print(f"Generating response with {chat_model} ...")
    answer = chat(
        api_key=openai_api_key,
        model=chat_model,
        system_prompt=system_prompt,
        context=context,
        history=history,
        question=question,
    )

    # ── save to memory ─────────────────────────────────────────────────────
    history = append_exchange(history, question, answer)
    save_memory(MEMORY_PATH, history, max_pairs=max_history)

    # ── write output ───────────────────────────────────────────────────────
    OUTPUT_PATH.write_text(answer, encoding="utf-8")

    print(f"\nAnswer written to {OUTPUT_PATH}")
    print("-" * 50)
    print(answer)


if __name__ == "__main__":
    main()
