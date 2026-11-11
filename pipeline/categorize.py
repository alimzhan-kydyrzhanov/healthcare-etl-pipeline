"""GenAI-шаг: классифицирует свободный текст заметки врача в категорию.

Если задан ANTHROPIC_API_KEY и USE_LLM=1 — спрашиваем LLM (Claude).
Иначе — простые правила. Пайплайн работает в обоих режимах, поэтому тесты и CI не зависят от API.
"""
import os
from functools import lru_cache

CATEGORIES = ["post_operative", "follow_up", "routine", "symptom", "none"]

RULES = [
    ("post_operative", ("surgery", "post-op")),
    ("follow_up", ("follow-up", "refer", "recommended")),
    ("symptom", ("pain", "sensitivity")),
    ("routine", ("routine",)),
]


def _rules(note: str) -> str:
    text = note.lower()
    for category, words in RULES:
        if any(w in text for w in words):
            return category
    return "none"


@lru_cache(maxsize=1024)  # одинаковые заметки не отправляем в API повторно
def _llm(note: str) -> str:
    from anthropic import Anthropic
    msg = Anthropic().messages.create(
        model=os.getenv("CLAUDE_MODEL", "claude-haiku-5-5"),
        max_tokens=10,
        messages=[{"role": "user", "content":
                   f"Classify this clinical note into exactly one of {CATEGORIES}. "
                   f"Answer with the category only.\nNote: {note}"}],
    )
    answer = msg.content[0].text.strip().lower()
    return answer if answer in CATEGORIES else _rules(note)  # LLM ошибся -> откат на правила


def categorize_note(note: str) -> str:
    if not note.strip():
        return "none"
    if os.getenv("USE_LLM") == "1" and os.getenv("ANTHROPIC_API_KEY"):
        return _llm(note)
    return _rules(note)
