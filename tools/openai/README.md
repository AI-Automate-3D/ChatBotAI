# tools/openai/

OpenAI utilities for knowledge base embedding and ingestion.

## Files

| File | Description |
|------|-------------|
| `OpenAI_embeddings.py` | Parse `.docx` knowledge base documents, embed with OpenAI, and upsert to Pinecone |

## OpenAI_embeddings.py

All-in-one tool for embedding knowledge base documents into Pinecone. Supports both interactive and CLI modes.

### What it does

1. Parses a `.docx` knowledge base file into chunks (using `--- KB_CHUNK_END ---` separators)
2. Selects an embedding model (small: 1536 dims or large: 3072 dims)
3. Validates the Pinecone index dimensions (recreates if mismatched with `--replace`)
4. Embeds each chunk via OpenAI
5. Upserts the vectors into Pinecone in batches of 100

### Usage

```bash
# Interactive mode — prompts for file and model selection
python tools/openai/OpenAI_embeddings.py

# CLI mode
python tools/openai/OpenAI_embeddings.py --file __test_data/Jaded\ Rose/kb.docx --model small

# Replace existing index if dimensions differ
python tools/openai/OpenAI_embeddings.py --file kb.docx --model large --replace
```

### CLI Arguments

| Argument | Description |
|----------|-------------|
| `--file` | Path to `.docx` knowledge base file |
| `--model` | Embedding model: `small` (1536d) or `large` (3072d) |
| `--replace` | Delete and recreate Pinecone index if dimensions don't match |

### Configuration

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
  }
}
```

### Dependencies

- `openai`
- `pinecone` (via `tools/pinecone/`)
- `python-docx`
