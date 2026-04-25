import anthropic
from pydantic import BaseModel

client = anthropic.Anthropic()


# ── language detection ─────────────────────────────────────────────────────────

def script(text: str) -> str:
    """Return 'greek', 'cyrillic', or 'other' based on the majority script."""
    greek = cyrillic = 0
    for ch in text:
        cp = ord(ch)
        if 0x0370 <= cp <= 0x03FF or 0x1F00 <= cp <= 0x1FFF:
            greek += 1
        elif 0x0400 <= cp <= 0x04FF:
            cyrillic += 1
    if greek > cyrillic:
        return "greek"
    if cyrillic > greek:
        return "cyrillic"
    return "other"


# ── explain a Greek word / phrase ──────────────────────────────────────────────

class GreekExplanation(BaseModel):
    explanation: str      # full plain-text explanation in Russian with emoji section headers
    card_normalized: str  # canonical Greek form for the flashcard front
    card_translation: str # primary Russian translation for the flashcard back


_EXPLAIN_PROMPT = """\
You are a Greek language expert who teaches Greek to Russian speakers.

The user wants to understand: «{word}»

Write a detailed explanation IN RUSSIAN using exactly this structure (plain text, emoji as section markers, no markdown):

📖 {word} — <brief primary translation>

🔤 Переводы
All meaningful Russian translations with nuance notes (when each applies).

🏛 Происхождение
Etymology within Greek: ancient/Byzantine/Modern Greek roots, key morphemes.

🌍 В других языках
Russian or English words derived from this Greek root. Write "нет заимствований" if none.

🔗 Синонимы в греческом
Greek words/phrases with similar meaning, each with a short Russian gloss.

👀 Похожие по написанию
Greek words that look or sound similar but carry a different meaning. Write "нет" if none.

Keep each section concise and practical.

Also fill:
- card_normalized: canonical dictionary form (verb → infinitive, noun → nominative singular, idiom → citation form)
- card_translation: the most common Russian translation, short enough for a flashcard
"""


def explain_greek(word: str) -> GreekExplanation:
    response = client.messages.parse(
        model="claude-opus-4-7",
        max_tokens=2048,
        messages=[{"role": "user", "content": _EXPLAIN_PROMPT.format(word=word.strip())}],
        output_format=GreekExplanation,
    )
    return response.parsed_output


# ── translate a Russian word / phrase to Greek ─────────────────────────────────

class GreekOption(BaseModel):
    greek: str       # normalized Greek word/phrase
    translation: str # concise Russian gloss for the card back


class RussianToGreek(BaseModel):
    overview: str            # explanation in Russian of the options and their nuances
    options: list[GreekOption]


_TRANSLATE_PROMPT = """\
You are a Greek language expert who teaches Greek to Russian speakers.

The user wants to express in Modern Greek: «{word}»

Write IN RUSSIAN:
A short overview (2–4 sentences) of the possible Greek translations and when each is used.

Then fill the `options` list — one entry per distinct Greek translation, with:
- greek: the normalized Greek form
- translation: a concise Russian gloss suitable for a flashcard back

Keep the overview practical and concise. Plain text, no markdown.
"""


def translate_russian(word: str) -> RussianToGreek:
    response = client.messages.parse(
        model="claude-opus-4-7",
        max_tokens=1024,
        messages=[{"role": "user", "content": _TRANSLATE_PROMPT.format(word=word.strip())}],
        output_format=RussianToGreek,
    )
    return response.parsed_output


# ── compare 2–3 Greek words ────────────────────────────────────────────────────

class Comparison(BaseModel):
    comparison: str  # plain-text explanation in Russian


_COMPARE_PROMPT = """\
You are a Greek language expert who teaches Greek to Russian speakers.

Compare these Greek words / phrases and explain the differences IN RUSSIAN:

{words}

Cover: meaning differences, connotation, register/formality, grammatical notes, typical contexts.
Include short example sentences where helpful. Plain text, no markdown.
"""


def compare_greek(words: list[str]) -> str:
    bullet_list = "\n".join(f"• {w}" for w in words)
    response = client.messages.parse(
        model="claude-opus-4-7",
        max_tokens=1024,
        messages=[{"role": "user", "content": _COMPARE_PROMPT.format(words=bullet_list)}],
        output_format=Comparison,
    )
    return response.parsed_output.comparison
