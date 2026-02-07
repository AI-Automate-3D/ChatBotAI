"""Generate project specification PDF report."""

from fpdf import FPDF

FONT_DIR = "/usr/share/fonts/truetype/dejavu"


class Report(FPDF):
    DARK = (30, 30, 30)
    MID = (80, 80, 80)
    ACCENT = (0, 102, 204)
    LIGHT_BG = (245, 245, 245)
    WHITE = (255, 255, 255)
    RULE = (200, 200, 200)

    def __init__(self):
        super().__init__()
        self.add_font("DejaVu", "", f"{FONT_DIR}/DejaVuSans.ttf", uni=True)
        self.add_font("DejaVu", "B", f"{FONT_DIR}/DejaVuSans-Bold.ttf", uni=True)
        self.add_font("DejaVuMono", "", f"{FONT_DIR}/DejaVuSansMono.ttf", uni=True)
        self.add_font("DejaVuMono", "B", f"{FONT_DIR}/DejaVuSansMono-Bold.ttf", uni=True)
        self.add_font("DejaVuSerif", "", f"{FONT_DIR}/DejaVuSerif.ttf", uni=True)
        self.add_font("DejaVuSerif", "B", f"{FONT_DIR}/DejaVuSerif-Bold.ttf", uni=True)

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("DejaVu", "I" if False else "", 8)
        self.set_text_color(*self.MID)
        self.cell(0, 8, "ChatBotAI - Project Specification", align="L")
        self.cell(0, 8, f"Page {self.page_no()}", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*self.RULE)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def footer(self):
        if self.page_no() == 1:
            self.set_y(-25)
            self.set_font("DejaVu", "", 8)
            self.set_text_color(*self.MID)
            self.cell(0, 5, "AI-Automate-3D  |  github.com/AI-Automate-3D/ChatBotAI", align="C", new_x="LMARGIN", new_y="NEXT")
            self.cell(0, 5, "Confidential", align="C")

    def title_page(self):
        self.add_page()
        self.ln(50)
        self.set_font("DejaVu", "B", 32)
        self.set_text_color(*self.DARK)
        self.cell(0, 14, "ChatBotAI", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)
        self.set_font("DejaVu", "", 16)
        self.set_text_color(*self.MID)
        self.cell(0, 10, "Project Specification", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(8)
        self.set_draw_color(*self.ACCENT)
        self.set_line_width(0.8)
        cx = self.w / 2
        self.line(cx - 40, self.get_y(), cx + 40, self.get_y())
        self.set_line_width(0.2)
        self.ln(12)
        self.set_font("DejaVu", "", 11)
        self.set_text_color(*self.MID)
        lines = [
            "Modular AI Toolkit & Integration Platform",
            "",
            "Version 0.5",
            "February 2026",
            "",
            "A collection of standalone, independently importable modules",
            "for Telegram, Gmail, OpenAI, and Pinecone - designed to be",
            "composed into agentic workflows.",
        ]
        for line in lines:
            self.cell(0, 7, line, align="C", new_x="LMARGIN", new_y="NEXT")

    def section(self, title):
        self.ln(6)
        self.set_font("DejaVu", "B", 14)
        self.set_text_color(*self.ACCENT)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*self.ACCENT)
        self.set_line_width(0.5)
        self.line(self.l_margin, self.get_y(), self.l_margin + 60, self.get_y())
        self.set_line_width(0.2)
        self.ln(4)

    def subsection(self, title):
        self.ln(3)
        self.set_font("DejaVu", "B", 11)
        self.set_text_color(*self.DARK)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body(self, text):
        self.set_font("DejaVu", "", 10)
        self.set_text_color(*self.MID)
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def bullet(self, text):
        self.set_font("DejaVu", "", 9)
        self.set_text_color(*self.MID)
        x = self.l_margin
        w = self.w - self.l_margin - self.r_margin
        self.set_x(x)
        self.multi_cell(w, 5, "    -  " + text)

    def code_block(self, text):
        self.ln(2)
        self.set_fill_color(*self.LIGHT_BG)
        self.set_font("DejaVuMono", "", 8)
        self.set_text_color(*self.DARK)
        lines = text.strip().split("\n")
        for line in lines:
            self.cell(0, 5, f"  {line}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def table_row(self, cols, widths, bold=False, header=False):
        style = "B" if bold else ""
        self.set_font("DejaVu", style, 8)
        if header:
            self.set_fill_color(*self.ACCENT)
            self.set_text_color(*self.WHITE)
        else:
            self.set_fill_color(*self.WHITE)
            self.set_text_color(*self.MID)
        h = 7
        for col, w in zip(cols, widths):
            self.cell(w, h, f" {col}", border=1, fill=True)
        self.ln()

    def kv(self, key, value):
        self.set_font("DejaVu", "B", 10)
        self.set_text_color(*self.DARK)
        self.cell(45, 6, key + ":")
        self.set_font("DejaVu", "", 10)
        self.set_text_color(*self.MID)
        self.cell(0, 6, value, new_x="LMARGIN", new_y="NEXT")


def build():
    pdf = Report()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ── TITLE PAGE ─────────────────────────────────────────────────────────
    pdf.title_page()

    # ── TABLE OF CONTENTS ──────────────────────────────────────────────────
    pdf.add_page()
    pdf.section("Table of Contents")
    toc = [
        "1.  Project Overview",
        "2.  Architecture",
        "3.  Deliverables",
        "    3.1  Telegram Integration (tg/)",
        "    3.2  Gmail Integration (gmail/)",
        "    3.3  RAG Agent (agent/)",
        "    3.4  Pinecone Toolkit (tools/pinecone/)",
        "    3.5  OpenAI Ingestion (tools/openai/)",
        "4.  Tasks Completed",
        "5.  Technical Specifications",
        "6.  Configuration",
        "7.  Dependencies",
        "8.  File Manifest",
    ]
    for item in toc:
        pdf.body(item)

    # ── 1. PROJECT OVERVIEW ────────────────────────────────────────────────
    pdf.add_page()
    pdf.section("1. Project Overview")
    pdf.body(
        "ChatBotAI is a modular toolkit of standalone API functions, processing pipelines, "
        "and AI agent components. Every module is independently importable and designed to be "
        "composed into agentic workflows in a separate project."
    )
    pdf.body(
        "The project provides production-ready integrations for Telegram, Gmail, OpenAI, and "
        "Pinecone, connected through a consistent 3-stage pipeline architecture using JSON queue "
        "files as the inter-process communication layer."
    )

    pdf.subsection("Key Principles")
    for p in [
        "Standalone modules - each .py file can be imported and used independently",
        "Decoupled pipeline - triggers, handlers, and actions run as separate processes",
        "JSON queue data layer - inter-stage communication via JSON files on disk",
        "UUID correlation IDs - every message is tracked across the full pipeline",
        "Provider-agnostic - embedding functions, LLM providers, and vector stores are pluggable",
        "No namespace collisions - package named tg/ to avoid shadowing python-telegram-bot",
    ]:
        pdf.bullet(p)

    # ── 2. ARCHITECTURE ────────────────────────────────────────────────────
    pdf.ln(4)
    pdf.section("2. Architecture")
    pdf.subsection("Repository Structure")
    pdf.code_block(
        "ChatBotAI/\n"
        "+-- tg/              Telegram Bot - API functions & message pipeline\n"
        "+-- gmail/           Gmail - API functions & email pipeline\n"
        "+-- agent/           RAG chatbot - OpenAI + Pinecone retrieval\n"
        "+-- tools/\n"
        "|   +-- pinecone/    Vector database toolkit & CLI\n"
        "|   +-- openai/      Embedding & knowledge base ingestion\n"
        "+-- _config files/   Configuration templates\n"
        "+-- credentials/     OAuth tokens (gitignored)"
    )

    pdf.subsection("Pipeline Architecture")
    pdf.body(
        "Both tg/ and gmail/ implement a 3-stage pipeline. Each stage is a standalone "
        "script that reads from and writes to JSON queue files:"
    )
    pdf.code_block(
        "triggers/              handlers/              actions/\n"
        "(external input)  -->  (process & respond)  -->  (send output)\n"
        "                  |                          |\n"
        "         trigger_queue.json          reply_queue.json"
    )

    w = [48, 60, 60]
    pdf.table_row(["Stage", "Telegram", "Gmail"], w, header=True)
    pdf.table_row(["Triggers", "Bot listener", "Inbox poller (IMAP/API)"], w)
    pdf.table_row(["Handlers", "Build reply payloads", "Build reply payloads"], w)
    pdf.table_row(["Actions", "Send via Bot API", "Send via Gmail API"], w)

    # ── 3. DELIVERABLES ───────────────────────────────────────────────────
    pdf.add_page()
    pdf.section("3. Deliverables")

    # 3.1 Telegram
    pdf.subsection("3.1  Telegram Integration (tg/)")
    pdf.body("Standalone API wrappers and a message processing pipeline for Telegram bots.")

    w2 = [50, 118]
    pdf.table_row(["Module", "Description"], w2, header=True)
    pdf.table_row(["api/send_message.py", "Send a text message (sync + async)"], w2)
    pdf.table_row(["api/send_typing.py", "Send typing indicator (sync + async)"], w2)
    pdf.table_row(["api/get_me.py", "Get bot info (sync + async)"], w2)
    pdf.table_row(["utils/config.py", "Load config from JSON or env vars"], w2)
    pdf.table_row(["utils/chat_logger.py", "JSONL audit logger for updates"], w2)
    pdf.table_row(["utils/queue_manager.py", "JSON queue: load, save, append, clear"], w2)
    pdf.table_row(["triggers/bot.py", "Bot listener - queues incoming messages"], w2)
    pdf.table_row(["handlers/build_replies.py", "Trigger queue -> reply queue"], w2)
    pdf.table_row(["actions/send_replies.py", "Reply queue -> send via Bot API"], w2)

    # 3.2 Gmail
    pdf.ln(4)
    pdf.subsection("3.2  Gmail Integration (gmail/)")
    pdf.body("Standalone Gmail API functions and an email processing pipeline using OAuth2.")

    pdf.table_row(["Module", "Description"], w2, header=True)
    pdf.table_row(["utils/auth.py", "OAuth2 flow: authorize, refresh, build service"], w2)
    pdf.table_row(["utils/parser.py", "Parse messages: MIME, HTML, headers, attachments"], w2)
    pdf.table_row(["utils/queue_manager.py", "JSON queue manager (same interface as tg/)"], w2)
    pdf.table_row(["api/get_email.py", "Fetch single email by ID with parsing"], w2)
    pdf.table_row(["api/list_emails.py", "Search/list with Gmail query syntax"], w2)
    pdf.table_row(["api/send_email.py", "Send email with attachments, CC, BCC, HTML"], w2)
    pdf.table_row(["api/reply_email.py", "Reply to existing thread"], w2)
    pdf.table_row(["api/modify_labels.py", "Mark read/unread, archive, trash, star"], w2)
    pdf.table_row(["api/get_attachments.py", "Download attachments from a message"], w2)
    pdf.table_row(["triggers/poll_inbox.py", "Poll unread inbox -> trigger_queue.json"], w2)
    pdf.table_row(["handlers/build_replies.py", "Trigger queue -> reply queue"], w2)
    pdf.table_row(["actions/send_replies.py", "Reply queue -> send via Gmail API"], w2)

    # 3.3 Agent
    pdf.add_page()
    pdf.subsection("3.3  RAG Agent (agent/)")
    pdf.body(
        "Retrieval-Augmented Generation chatbot. Embeds user questions, retrieves "
        "context from a Pinecone vector store, and generates responses via OpenAI."
    )

    pdf.table_row(["Module", "Description"], w2, header=True)
    pdf.table_row(["memory.py", "Conversation history: load, save, clear, append, trim"], w2)
    pdf.table_row(["context.py", "Embed questions + query Pinecone for context"], w2)
    pdf.table_row(["chat.py", "OpenAI chat: chat(), chat_simple(), build_messages()"], w2)
    pdf.table_row(["prompt.py", "System prompt loader: .txt, .docx, or inline"], w2)
    pdf.table_row(["agent.py", "Orchestrator: memory + context + chat in one flow"], w2)

    # 3.4 Pinecone
    pdf.ln(4)
    pdf.subsection("3.4  Pinecone Toolkit (tools/pinecone/)")
    pdf.body(
        "Full-featured, self-contained Pinecone vector database toolkit. Can be copied "
        "into any project. Includes a unified CLI."
    )

    pdf.table_row(["Module", "Description"], w2, header=True)
    pdf.table_row(["config.py", "PineconeConfig: from_json(), from_env()"], w2)
    pdf.table_row(["client.py", "Authenticated client/index factory"], w2)
    pdf.table_row(["vector_store.py", "Upsert, query (filters), batch, fetch, stats"], w2)
    pdf.table_row(["index_manager.py", "Create, delete, list, describe indexes"], w2)
    pdf.table_row(["embeddings.py", "embed_text(), embed_batch(), make_embed_fn()"], w2)
    pdf.table_row(["parser.py", "Parse .docx, .txt, .csv into chunks"], w2)
    pdf.table_row(["fetch.py", "fetch_vectors(), fetch_one(), vector_exists()"], w2)
    pdf.table_row(["namespace_manager.py", "List, delete, copy, stats for namespaces"], w2)
    pdf.table_row(["backup.py", "Export/import to JSON, metadata-only export"], w2)
    pdf.table_row(["cli.py", "Unified CLI: index, vectors, namespace, backup"], w2)

    # 3.5 OpenAI
    pdf.ln(4)
    pdf.subsection("3.5  OpenAI Ingestion (tools/openai/)")
    pdf.body(
        "One-file runner for embedding .docx knowledge bases and upserting to Pinecone. "
        "Supports interactive and CLI modes with auto index dimension validation."
    )

    # ── 4. TASKS COMPLETED ─────────────────────────────────────────────────
    pdf.add_page()
    pdf.section("4. Tasks Completed")

    tasks = [
        ("v0.3 - Telegram Refactor", [
            "Restructured telegram/ into modular tg/ package with triggers/, api/, handlers/, actions/, utils/",
            "Built standalone API wrappers: send_message, send_typing, get_me (sync + async)",
            "Implemented JSON queue pipeline: trigger_queue.json and reply_queue.json",
            "Created shared utilities: config loader, JSONL audit logger, generic queue manager",
            "Added UUID correlation IDs to track messages across pipeline stages",
            "Renamed input/ to triggers/ for clarity",
        ]),
        ("Agent Modules", [
            "Built agent/memory.py - conversation history management with configurable max pairs",
            "Built agent/context.py - Pinecone vector search with OpenAI embeddings",
            "Built agent/chat.py - OpenAI chat completion with RAG context injection",
            "Built agent/prompt.py - system prompt loader supporting .txt, .docx, and inline strings",
            "Refactored agent/agent.py to use new modular components",
        ]),
        ("Documentation", [
            "Created README.md in every package and subfolder (16 files)",
            "Wrote top-level README.md with setup, structure, and usage documentation",
            "Added docstrings to every public function and class",
        ]),
        ("Repo-Wide Fixes & Optimisations", [
            "CRITICAL: Renamed telegram/ to tg/ to resolve namespace collision with python-telegram-bot",
            "Added missing __init__.py for agent/ and tools/openai/",
            "Moved logging.basicConfig() from module level to main() functions",
            "Added null guard on message/text in bot trigger handler",
            "Propagated trigger entry UUIDs through to reply queue entries",
            "Fixed agent load_config to private _load_config to avoid import conflicts",
            "Fixed tools/pinecone/cli.py relative path to use absolute project root path",
            "Fixed make_embed_fn return type annotation",
            "Updated all internal imports from telegram.* to tg.*",
            "Updated .gitignore for tg/ paths and runtime data",
        ]),
        ("v0.4 - Gmail Integration", [
            "Built gmail/utils/auth.py - full OAuth2 flow with token caching and auto-refresh",
            "Built gmail/utils/parser.py - MIME tree walker, HTML stripping, attachment metadata",
            "Built gmail/api/ - 6 standalone API modules: get, list, send, reply, labels, attachments",
            "Built gmail/triggers/poll_inbox.py - polls unread inbox, queues messages, marks as read",
            "Built gmail/handlers/build_replies.py - processes trigger queue with pluggable reply logic",
            "Built gmail/actions/send_replies.py - sends threaded replies or new emails from queue",
            "Added Gmail config to config.example.json and .gitignore",
        ]),
        ("v0.5 - Pinecone Toolkit Expansion", [
            "Built tools/pinecone/embeddings.py - embed_text(), embed_batch(), make_embed_fn()",
            "Built tools/pinecone/fetch.py - fetch_vectors(), fetch_one(), vector_exists()",
            "Built tools/pinecone/namespace_manager.py - list, delete, copy, stats for namespaces",
            "Built tools/pinecone/backup.py - export/import vectors to JSON, metadata-only export",
            "Expanded parser.py - added .txt (paragraph splitting) and .csv parsing, parse_file() auto-detect",
            "Expanded vector_store.py - metadata filtering on queries, batch query, min_score, fetch method",
            "Expanded cli.py - new command groups: vectors fetch/query, namespace, backup",
            "Updated __init__.py with all new exports",
        ]),
    ]

    for title, items in tasks:
        pdf.subsection(title)
        for item in items:
            pdf.bullet(item)
        pdf.ln(2)

    # ── 5. TECHNICAL SPECIFICATIONS ────────────────────────────────────────
    pdf.add_page()
    pdf.section("5. Technical Specifications")

    pdf.subsection("Language & Runtime")
    pdf.kv("Language", "Python 3.10+")
    pdf.kv("Type Hints", "PEP 604 union syntax (str | None)")
    pdf.kv("Async Support", "Telegram API functions provide sync + async variants")

    pdf.ln(4)
    pdf.subsection("Data Interchange")
    pdf.kv("Queue Format", "JSON files (array of objects)")
    pdf.kv("Audit Log", "JSONL (append-only, one JSON object per line)")
    pdf.kv("Config", "JSON file or environment variables (.env)")
    pdf.kv("Correlation", "UUID v4 IDs assigned at trigger, propagated through pipeline")

    pdf.ln(4)
    pdf.subsection("Authentication")
    pdf.kv("Telegram", "Bot token via config.json or TELEGRAM_BOT_TOKEN env var")
    pdf.kv("Gmail", "OAuth2 with auto-refresh (credentials.json + token.json)")
    pdf.kv("OpenAI", "API key via config.json or OPENAI_API_KEY env var")
    pdf.kv("Pinecone", "API key via config.json or PINECONE_API_KEY env var")

    pdf.ln(4)
    pdf.subsection("Embedding Models")
    w3 = [55, 40, 73]
    pdf.table_row(["Model", "Dimensions", "Alias"], w3, header=True)
    pdf.table_row(["text-embedding-3-small", "1536", '"small"'], w3)
    pdf.table_row(["text-embedding-3-large", "3072", '"large"'], w3)

    pdf.ln(4)
    pdf.subsection("Pinecone CLI Commands")
    w4 = [40, 128]
    pdf.table_row(["Group", "Commands"], w4, header=True)
    pdf.table_row(["index", "create, delete, list, describe"], w4)
    pdf.table_row(["vectors", "stats, upsert, fetch, query, delete, delete-all, update-metadata"], w4)
    pdf.table_row(["namespace", "list, stats, delete, copy"], w4)
    pdf.table_row(["backup", "export, import"], w4)

    # ── 6. CONFIGURATION ──────────────────────────────────────────────────
    pdf.ln(6)
    pdf.section("6. Configuration")
    pdf.body("Settings can be provided via _config files/config.json or environment variables (.env):")

    w5 = [35, 52, 48, 33]
    pdf.table_row(["Service", "Config Key", "Env Variable", "Required"], w5, header=True)
    pdf.table_row(["Telegram", "telegram.bot_token", "TELEGRAM_BOT_TOKEN", "For tg/"], w5)
    pdf.table_row(["OpenAI", "openai.api_key", "OPENAI_API_KEY", "For agent/"], w5)
    pdf.table_row(["Pinecone", "pinecone.api_key", "PINECONE_API_KEY", "For vectors"], w5)
    pdf.table_row(["Gmail", "gmail.credentials_file", "GOOGLE_CLIENT_ID", "For gmail/"], w5)
    pdf.table_row(["Agent", "agent.chat_model", "OPENAI_CHAT_MODEL", "Optional"], w5)

    # ── 7. DEPENDENCIES ───────────────────────────────────────────────────
    pdf.add_page()
    pdf.section("7. Dependencies")

    pdf.subsection("Core")
    for dep in [
        "python-telegram-bot - Telegram Bot API framework",
        "openai - OpenAI API client (chat, embeddings)",
        "pinecone - Pinecone vector database client",
    ]:
        pdf.bullet(dep)

    pdf.subsection("Gmail")
    for dep in [
        "google-api-python-client - Google API client library",
        "google-auth-httplib2 - HTTP transport for Google Auth",
        "google-auth-oauthlib - OAuth2 integration",
    ]:
        pdf.bullet(dep)

    pdf.subsection("Parsing")
    for dep in [
        "python-docx - .docx document parsing",
    ]:
        pdf.bullet(dep)

    pdf.subsection("Optional")
    for dep in [
        "python-dotenv - .env file loading",
    ]:
        pdf.bullet(dep)

    # ── 8. FILE MANIFEST ──────────────────────────────────────────────────
    pdf.ln(4)
    pdf.section("8. File Manifest")

    manifest = {
        "tg/": [
            "__init__.py, README.md",
            "api/__init__.py, send_message.py, send_typing.py, get_me.py",
            "triggers/__init__.py, bot.py",
            "handlers/__init__.py, build_replies.py",
            "actions/__init__.py, send_replies.py",
            "utils/__init__.py, config.py, chat_logger.py, queue_manager.py",
        ],
        "gmail/": [
            "__init__.py, README.md",
            "api/__init__.py, get_email.py, list_emails.py, send_email.py, reply_email.py, modify_labels.py, get_attachments.py",
            "triggers/__init__.py, poll_inbox.py",
            "handlers/__init__.py, build_replies.py",
            "actions/__init__.py, send_replies.py",
            "utils/__init__.py, auth.py, parser.py, queue_manager.py",
        ],
        "agent/": [
            "__init__.py, README.md",
            "agent.py, memory.py, context.py, chat.py, prompt.py",
        ],
        "tools/pinecone/": [
            "__init__.py, README.md",
            "config.py, client.py, vector_store.py, index_manager.py",
            "embeddings.py, parser.py, fetch.py, namespace_manager.py, backup.py, cli.py",
        ],
        "tools/openai/": [
            "__init__.py, README.md, OpenAI_embeddings.py",
        ],
        "Root": [
            "README.md, README.pdf, .gitignore, .env.example",
            "_config files/config.example.json",
        ],
    }

    for pkg, files in manifest.items():
        pdf.subsection(pkg)
        for f in files:
            pdf.set_font("DejaVuMono", "", 8)
            pdf.set_text_color(*pdf.MID)
            pdf.cell(0, 5, f"  {f}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    # ── OUTPUT ─────────────────────────────────────────────────────────────
    output_path = "/home/user/ChatBotAI/README.pdf"
    pdf.output(output_path)
    print(f"PDF saved to {output_path}")
    return output_path


if __name__ == "__main__":
    build()
