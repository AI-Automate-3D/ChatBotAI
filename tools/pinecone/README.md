# tools/pinecone/

Reusable Pinecone vector database toolkit. Self-contained — can be copied into any project.

## Files

| File | Key Exports | Description |
|------|-------------|-------------|
| `config.py` | `PineconeConfig` | Configuration dataclass with `from_json()` and `from_env()` factory methods |
| `client.py` | `get_client()`, `get_index()` | Thin wrappers for authenticated Pinecone client/index creation |
| `vector_store.py` | `VectorStore` | Core vector operations — upsert, query, delete, stats |
| `index_manager.py` | `create_index()`, `delete_index()`, `list_indexes()`, `describe_index()` | Index lifecycle management |
| `parser.py` | `parse_docx()`, `parse_kb_text()` | Parse `.docx` knowledge base documents into chunks |
| `cli.py` | — | Unified CLI for all Pinecone operations |

## VectorStore

The main interface for working with vectors. Embedding-agnostic — pass any `embed_fn` callable.

```python
from tools.pinecone.config import PineconeConfig
from tools.pinecone.vector_store import VectorStore

config = PineconeConfig.from_json("config.json")
store = VectorStore(config, embed_fn=my_embed_fn)

# Upsert text (auto-embeds)
store.upsert_texts([
    {"id": "doc-1", "text": "Returns policy..."},
    {"id": "doc-2", "text": "Shipping info..."},
])

# Query with text (auto-embeds)
results = store.query_text("How do returns work?", top_k=5)

# Get formatted context for LLM
context = store.get_context("How do returns work?", top_k=5)
# -> "[1] Returns policy...\n\n[2] Related text..."

# Stats
stats = store.stats()
```

## PineconeConfig

```python
from tools.pinecone.config import PineconeConfig

# From config.json
config = PineconeConfig.from_json("config.json")

# From environment variables
config = PineconeConfig.from_env()

# Direct
config = PineconeConfig(
    api_key="pk-...",
    index_name="my-index",
    namespace="chatbot",
)
```

## Index Management

```python
from tools.pinecone.index_manager import create_index, delete_index, describe_index

create_index(config, dimension=1536, metric="cosine")
info = describe_index(config)
delete_index(config, skip_confirm=True)
```

## Document Parsing

Parses `.docx` files using `--- KB_CHUNK_END ---` as the separator. Each chunk should have `KB_ID`, `TYPE`, `TITLE`, and `TEXT` fields.

```python
from tools.pinecone.parser import parse_docx

chunks = parse_docx("knowledge_base.docx")
# -> [{"id": "kb_001", "text": "...", "type": "support", "title": "..."}, ...]
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
python -m tools.pinecone.cli vectors delete --ids vec-1 vec-2
python -m tools.pinecone.cli vectors delete-all --yes
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
- `python-docx` (for `.docx` parsing)
