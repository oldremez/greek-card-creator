import base64
import anthropic
from pydantic import BaseModel

client = anthropic.Anthropic()

EXTRACTION_PROMPT = """You are a Greek language expert. Analyze the image and extract all Greek words and phrases visible in it.

For each Greek word or phrase:
1. Provide the normalized (dictionary/lemma) form — e.g. verb in infinitive, noun in nominative singular
2. Provide the Russian translation
3. Record the original form exactly as it appears in the image (inflected/conjugated form)

Focus on meaningful vocabulary: nouns, verbs, adjectives, adverbs, set phrases. Skip punctuation and numerals.
If the original form and normalized form are identical, use the same value for both fields.
If no Greek text is found in the image, return an empty cards array."""


class FlashCard(BaseModel):
    normalized: str
    translation: str
    original: str


class FlashCards(BaseModel):
    cards: list[FlashCard]


def extract_greek_cards(image_bytes: bytes, media_type: str = "image/jpeg") -> list[FlashCard]:
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    response = client.messages.parse(
        model="claude-opus-4-7",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64,
                        },
                    },
                    {"type": "text", "text": EXTRACTION_PROMPT},
                ],
            }
        ],
        output_format=FlashCards,
    )

    if response.parsed_output is None:
        return []
    return response.parsed_output.cards
