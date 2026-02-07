# Agent

RAG (Retrieval-Augmented Generation) chatbot agent that answers questions using a Pinecone knowledge base and OpenAI chat completion.

## Architecture

The agent is split into standalone modules that can each be imported independently:

```
agent.py          Orchestrator — ties everything together
prompt.py         Load system prompts from .txt / .docx / inline
context.py        Embed questions and retrieve context from Pinecone
chat.py           Send RAG-augmented questions to OpenAI
memory.py         Conversation history management
```

## Files

| File | Key Functions | Description |
|------|---------------|-------------|
| `agent.py` | `main()` | Orchestrator — reads `input.txt`, runs the pipeline, writes `output.txt` |
| `prompt.py` | `load_prompt()` | Load system prompts from `.txt`, `.docx`, or inline strings |
| `context.py` | `retrieve_context()`, `retrieve_raw_results()`, `make_embed_fn()` | Embed questions via OpenAI and query Pinecone for relevant context |
| `chat.py` | `chat()`, `chat_simple()`, `build_messages()` | Send RAG-augmented questions to OpenAI with context and history |
| `memory.py` | `load_memory()`, `save_memory()`, `clear_memory()`, `append_exchange()` | JSON-file conversation history with auto-trimming |
| `system_prompt.txt` | — | Default system prompt for the customer support bot |

## Quick Start

```bash
# Write a question
echo "How do I return an item?" > agent/input.txt

# Run the agent
python agent/agent.py

# Read the answer
cat agent/output.txt

# Clear conversation memory
python agent/agent.py --clear
```

## Using Individual Modules

### prompt.py

```python
from agent.prompt import load_prompt

prompt = load_prompt("agent/system_prompt.txt")
prompt = load_prompt("agent/system_prompt.docx")
prompt = load_prompt(None, default="You are a helpful assistant.")
```

### context.py

```python
from agent.context import retrieve_context, make_embed_fn

# Full retrieval (embed + query + format)
context = retrieve_context(
    question="How do I return an item?",
    openai_api_key="sk-...",
    embedding_model="text-embedding-3-small",
    top_k=5,
)

# Just the embedding function
embed_fn = make_embed_fn("sk-...", "text-embedding-3-small")
vector = embed_fn("some text")  # -> list[float]
```

### chat.py

```python
from agent.chat import chat, chat_simple

# RAG chat with context and history
answer = chat(
    api_key="sk-...",
    model="gpt-4.1",
    system_prompt="You are helpful.",
    context="Knowledge base text here...",
    history=[{"role": "user", "content": "Hi"}],
    question="How do I return an item?",
)

# Simple one-shot question (no context, no history)
answer = chat_simple(
    api_key="sk-...",
    model="gpt-4.1",
    system_prompt="You are helpful.",
    question="What is 2+2?",
)
```

### memory.py

```python
from agent.memory import load_memory, save_memory, clear_memory, append_exchange

history = load_memory("memory.json")
history = append_exchange(history, "What is RAG?", "RAG stands for...")
save_memory("memory.json", history, max_pairs=10)
clear_memory("memory.json")
```

## Runtime Files (not committed)

| File | Description |
|------|-------------|
| `input.txt` | Question to answer (write before running) |
| `output.txt` | Agent's response (written after running) |
| `memory.json` | Conversation history (auto-managed) |

## Configuration

Requires these keys in `_config files/config.json`:

```json
{
  "openai": {
    "api_key": "sk-...",
    "embedding_model": "text-embedding-3-small"
  },
  "pinecone": {
    "api_key": "pk-...",
    "index_name": "my-index",
    "namespace": "chatbot"
  },
  "agent": {
    "chat_model": "gpt-4.1",
    "system_prompt_file": "agent/system_prompt.txt",
    "top_k": 5,
    "max_history": 10
  }
}
```

## Dependencies

- `openai`
- `pinecone` (via `tools/pinecone/`)
- `python-docx` (optional, for `.docx` prompt files)
