"""AI Agent package — RAG chatbot with memory, context retrieval, and chat completion.

Primary entry point:

    from agent.agent import run

    answer = run("How do I return an item?")

Standalone modules:

    from agent.memory import load_memory, save_memory, clear_memory
    from agent.context import retrieve_context, make_embed_fn
    from agent.chat import chat, chat_simple, build_messages
    from agent.prompt import load_prompt
"""
