"""Chat completion — send a RAG-augmented question to OpenAI.

Usage
-----
    from ChatBotGeneric.chat import chat

    answer = chat(
        api_key="sk-...",
        model="gpt-4.1",
        system_prompt="You are a helpful assistant.",
        context="Relevant knowledge base text...",
        history=[{"role": "user", "content": "Hi"}],
        question="How do I return an item?",
    )
"""

from __future__ import annotations

import logging

import openai

logger = logging.getLogger(__name__)


def build_messages(
    system_prompt: str,
    context: str,
    history: list[dict],
    question: str,
) -> list[dict]:
    """Build the message list for an OpenAI chat completion call.

    Parameters
    ----------
    system_prompt : str
        The system-level instruction.
    context : str
        Retrieved knowledge base context.  If empty, the context
        message is omitted.
    history : list[dict]
        Previous conversation messages.
    question : str
        The current user question.

    Returns
    -------
    list[dict]
        OpenAI-format message list ready for the API call.
    """
    messages = [{"role": "system", "content": system_prompt}]

    if context:
        messages.append({
            "role": "system",
            "content": (
                "Use the following knowledge base context to answer "
                "the user's question:\n\n" + context
            ),
        })

    messages.extend(history)
    messages.append({"role": "user", "content": question})

    return messages


def chat(
    api_key: str,
    model: str,
    system_prompt: str,
    context: str,
    history: list[dict],
    question: str,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    """Send a RAG-augmented question to OpenAI and return the response.

    Parameters
    ----------
    api_key : str
        OpenAI API key.
    model : str
        Chat model name (e.g. ``"gpt-4.1"``).
    system_prompt : str
        The system-level instruction.
    context : str
        Retrieved knowledge base context (can be empty).
    history : list[dict]
        Previous conversation messages.
    question : str
        The current user question.
    temperature : float | None
        Sampling temperature.
    max_tokens : int | None
        Maximum tokens in the response.

    Returns
    -------
    str
        The assistant's response text.
    """
    client = openai.OpenAI(api_key=api_key)
    messages = build_messages(system_prompt, context, history, question)

    kwargs: dict = {"model": model, "messages": messages}
    if temperature is not None:
        kwargs["temperature"] = temperature
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    response = client.chat.completions.create(**kwargs)
    answer = response.choices[0].message.content

    logger.info(
        "Chat completion: model=%s, messages=%d, response_len=%d",
        model,
        len(messages),
        len(answer),
    )
    return answer
