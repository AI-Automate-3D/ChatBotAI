# Tools

Reusable toolkits for external services. Each subfolder is a self-contained package that can be copied into other projects.

## Folders

| Folder | Description |
|--------|-------------|
| [openai/](openai/) | OpenAI utilities — embedding runner for knowledge base ingestion |
| [pinecone/](pinecone/) | Pinecone vector database toolkit — client, vector store, index management, document parsing, and CLI |

## openai/

One-file runner that parses `.docx` knowledge base documents and embeds/upserts them into Pinecone.

| File | Description |
|------|-------------|
| `OpenAI_embeddings.py` | Interactive or CLI-driven tool for embedding knowledge base documents |

```bash
# Interactive mode
python tools/openai/OpenAI_embeddings.py

# CLI mode
python tools/openai/OpenAI_embeddings.py --file kb.docx --model small --replace
```

## pinecone/

Full Pinecone toolkit with vector store operations, index management, document parsing, and a unified CLI.

See [pinecone/README.md](pinecone/) for detailed documentation.
