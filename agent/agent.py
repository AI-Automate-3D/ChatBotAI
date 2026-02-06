"""AI Agent — reads input.txt, queries the knowledge base, writes output.txt.

Uses the Pinecone vector store for RAG (Retrieval-Augmented Generation)
and OpenAI gpt-4.1 for chat completion.  Conversation history is stored
in memory.json so the agent remembers previous exchanges.

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

import openai

from tools.pinecone.config import PineconeConfig
from tools.pinecone.vector_store import VectorStore

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


# ── memory ──────────────────────────────────────────────────────────────────

def load_memory() -> list[dict]:
    """Load conversation history from memory.json.

    Returns a list of message dicts: [{"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}, ...]
    """
    if not MEMORY_PATH.exists():
        return []
    try:
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def save_memory(history: list[dict], max_history: int) -> None:
    """Save conversation history to memory.json, trimmed to max_history pairs.

    Args:
        history:     Full list of user/assistant message dicts.
        max_history: Max number of *message pairs* to keep (each pair =
                     1 user + 1 assistant message = 2 entries).
    """
    # Keep only the last N pairs (N * 2 individual messages)
    max_messages = max_history * 2
    trimmed = history[-max_messages:] if max_messages > 0 else []

    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(trimmed, f, indent=2, ensure_ascii=False)


def clear_memory() -> None:
    """Delete conversation history."""
    if MEMORY_PATH.exists():
        MEMORY_PATH.unlink()
    print("Memory cleared.")


# ── embedding ───────────────────────────────────────────────────────────────

def make_embed_fn(api_key: str, model: str):
    """Create an OpenAI embedding function."""
    client = openai.OpenAI(api_key=api_key)

    def embed(text: str) -> list[float]:
        response = client.embeddings.create(input=text, model=model)
        return response.data[0].embedding

    return embed


# ── chat ────────────────────────────────────────────────────────────────────

def chat(
    api_key: str,
    model: str,
    system_prompt: str,
    context: str,
    history: list[dict],
    question: str,
) -> str:
    """Send a RAG-augmented question to OpenAI with conversation history."""
    client = openai.OpenAI(api_key=api_key)

    messages = [
        {"role": "system", "content": system_prompt},
    ]

    if context:
        messages.append({
            "role": "system",
            "content": f"Use the following knowledge base context to answer the user's question:\n\n{context}",
        })

    # Add conversation history (previous exchanges)
    messages.extend(history)

    # Add current question
    messages.append({"role": "user", "content": question})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )

    return response.choices[0].message.content


# ── main ────────────────────────────────────────────────────────────────────

def main() -> None:
    # Handle --clear flag
    if "--clear" in sys.argv:
        clear_memory()
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

    # Load system prompt — from file (.txt or .docx) or inline string
    prompt_file = agent_cfg.get("system_prompt_file", "")
    if prompt_file:
        prompt_path = PROJECT_ROOT / prompt_file
        if not prompt_path.exists():
            sys.exit(f"ERROR: System prompt file not found: {prompt_path}")

        if prompt_path.suffix.lower() == ".docx":
            from docx import Document as DocxDocument
            doc = DocxDocument(str(prompt_path))
            system_prompt = "\n".join(p.text for p in doc.paragraphs).strip()
        else:
            system_prompt = prompt_path.read_text(encoding="utf-8").strip()

        logger.info("Loaded system prompt from %s", prompt_file)
    else:
        system_prompt = agent_cfg.get(
            "system_prompt",
            "You are a helpful assistant. Answer questions using only the "
            "provided context. If you don't know the answer, say so honestly.",
        )

    # ── read input ─────────────────────────────────────────────────────────
    if not INPUT_PATH.exists():
        sys.exit(f"ERROR: No input file found at {INPUT_PATH}")

    question = INPUT_PATH.read_text(encoding="utf-8").strip()
    if not question:
        sys.exit("ERROR: input.txt is empty.")

    print(f"Question: {question}")

    # ── load memory ────────────────────────────────────────────────────────
    history = load_memory()
    if history:
        pairs = len(history) // 2
        print(f"Memory: {pairs} previous exchange(s) loaded")

    # ── retrieve context from Pinecone ─────────────────────────────────────
    pinecone_cfg = PineconeConfig.from_json(str(CONFIG_PATH))
    embed_fn = make_embed_fn(openai_api_key, embedding_model)
    store = VectorStore(pinecone_cfg, embed_fn=embed_fn)

    print("Retrieving context from knowledge base ...")
    context = store.get_context(question, top_k=top_k)

    if context:
        logger.info("Retrieved %d context chunk(s).", context.count("["))
    else:
        logger.warning("No relevant context found in the knowledge base.")

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
    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": answer})
    save_memory(history, max_history)

    # ── write output ───────────────────────────────────────────────────────
    OUTPUT_PATH.write_text(answer, encoding="utf-8")

    print(f"\nAnswer written to {OUTPUT_PATH}")
    print("─" * 50)
    print(answer)


if __name__ == "__main__":
    main()
