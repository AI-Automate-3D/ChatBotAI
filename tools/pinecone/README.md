# tools/pinecone/

Reusable Pinecone vector database toolkit. Self-contained — can be copied into any project.

## Modules

| Module | Key Exports | Description |
|--------|-------------|-------------|
| `config.py` | `PineconeConfig` | Configuration dataclass with `from_json()` and `from_env()` |
| `client.py` | `get_client()`, `get_index()` | Authenticated Pinecone client/index creation |
| `vector_store.py` | `VectorStore` | Core operations — upsert, query (with filters), batch query, delete, fetch, stats |
| `index_manager.py` | `create_index()`, `delete_index()`, `list_indexes()`, `describe_index()` | Index lifecycle management |
| `embeddings.py` | `make_embed_fn()`, `embed_text()`, `embed_batch()` | Standalone embedding wrappers (OpenAI) |
| `parser.py` | `parse_file()`, `parse_docx()`, `parse_txt()`, `parse_csv()` | Parse .docx, .txt, .csv into upsert-ready chunks |
| `fetch.py` | `fetch_vectors()`, `fetch_one()`, `vector_exists()` | Fetch vectors by ID |
| `namespace_manager.py` | `list_namespaces()`, `delete_namespace()`, `copy_namespace()` | Namespace operations |
| `backup.py` | `export_namespace()`, `import_vectors()`, `export_metadata_only()` | Backup & restore to JSON |
| `cli.py` | — | Unified CLI for all operations |

## VectorStore

The main interface for working with vectors. Embedding-agnostic — pass any `embed_fn` callable.

```python
from tools.pinecone import PineconeConfig, VectorStore
from tools.pinecone.embeddings import make_embed_fn

config = PineconeConfig.from_env()
embed = make_embed_fn(model="text-embedding-3-small")
store = VectorStore(config, embed_fn=embed)

# Upsert text (auto-embeds)
store.upsert_texts([
    {"id": "doc-1", "text": "Returns policy..."},
    {"id": "doc-2", "text": "Shipping info..."},
])

# Query with text
results = store.query_text("How do returns work?", top_k=5)

# Query with metadata filtering
results = store.query_text(
    "shipping", top_k=5,
    filter={"type": {"$eq": "support"}},
)

# Batch query multiple questions
all_results = store.query_batch(
    ["shipping?", "returns?", "pricing?"], top_k=3,
)

# Get formatted context for LLM
context = store.get_context("How do returns work?", top_k=5, min_score=0.7)

# Fetch by ID
vectors = store.fetch(["doc-1", "doc-2"])

# Stats
stats = store.stats()
```

## Embeddings

Standalone embedding functions — usable anywhere, not tied to VectorStore.

```python
from tools.pinecone.embeddings import embed_text, embed_batch, make_embed_fn

# Single text
vector = embed_text("hello world", model="text-embedding-3-small")

# Batch (fewer API calls)
vectors = embed_batch(["hello", "world"], model="small")

# Reusable function
embed = make_embed_fn(model="small")
vec = embed("hello world")
```

## Document Parsing

Multiple format support — all return upsert-ready chunks.

```python
from tools.pinecone.parser import parse_file, parse_docx, parse_txt, parse_csv

# Auto-detect format by extension
chunks = parse_file("knowledge_base.docx")

# .docx with KB_CHUNK_END delimiters
chunks = parse_docx("knowledge_base.docx")

# .txt with delimiters or paragraph splitting
chunks = parse_txt("data.txt")

# .csv with id, text, and optional metadata columns
chunks = parse_csv("data.csv")
```

## Namespace Management

```python
from tools.pinecone.namespace_manager import list_namespaces, copy_namespace

# List all namespaces
ns = list_namespaces(config)  # {"chatbot": 150, "backup": 100}

# Copy between namespaces
copy_namespace(config, source_ns="chatbot", target_ns="backup")
```

## Backup & Restore

```python
from tools.pinecone.backup import export_namespace, import_vectors

# Export all vectors to JSON
export_namespace(config, output_file="backup.json")

# Export metadata only (no large embedding arrays)
export_metadata_only(config, output_file="metadata.json")

# Import from backup
import_vectors(config, input_file="backup.json", replace=True)
```

## CLI

```bash
# Index management
python -m tools.pinecone.cli index create --dimension 1536 --metric cosine
python -m tools.pinecone.cli index delete --yes
python -m tools.pinecone.cli index list
python -m tools.pinecone.cli index describe

# Vector operations
python -m tools.pinecone.cli vectors stats
python -m tools.pinecone.cli vectors upsert --file data.docx --replace
python -m tools.pinecone.cli vectors upsert --file data.csv
python -m tools.pinecone.cli vectors upsert --file data.txt
python -m tools.pinecone.cli vectors fetch --ids doc-1 doc-2
python -m tools.pinecone.cli vectors query --text "search terms" --top-k 5
python -m tools.pinecone.cli vectors query --text "search" --filter '{"type": {"$eq": "faq"}}'
python -m tools.pinecone.cli vectors delete --ids vec-1 vec-2
python -m tools.pinecone.cli vectors delete-all --yes

# Namespace operations
python -m tools.pinecone.cli namespace list
python -m tools.pinecone.cli namespace stats --ns chatbot
python -m tools.pinecone.cli namespace delete --ns old-data --yes
python -m tools.pinecone.cli namespace copy --from chatbot --to backup

# Backup & restore
python -m tools.pinecone.cli backup export --file backup.json
python -m tools.pinecone.cli backup export --file metadata.json --metadata-only
python -m tools.pinecone.cli backup import --file backup.json --replace
```

## Configuration

### config.json

```json
{
  "pinecone": {
    "api_key": "pk-...",
    "index_name": "my-index",
    "namespace": "chatbot",
    "cloud": "aws",
    "region": "us-east-1"
  }
}
```

### Environment Variables

| Variable | Required | Default |
|----------|----------|---------|
| `PINECONE_API_KEY` | yes | — |
| `PINECONE_INDEX_NAME` | yes | — |
| `PINECONE_NAMESPACE` | no | `"default"` |
| `PINECONE_CLOUD` | no | `"aws"` |
| `PINECONE_REGION` | no | `"us-east-1"` |

## Dependencies

- `pinecone`
- `openai` (for embeddings)
- `python-docx` (for `.docx` parsing)
