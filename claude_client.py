import base64
import anthropic
from pydantic import BaseModel

client = anthropic.Anthropic()

EXTRACTION_PROMPT = """You are a Greek language expert. Analyze the image and extract Greek vocabulary and expressions visible in it.

**Idioms and multi-word expressions come first.**
If two or more words form a fixed expression, idiom, or collocation — e.g. «αν και», «έτσι κι αλλιώς», «μια χαρά», «παρά πολύ», «από τότε που» — treat the whole expression as ONE entry. Do NOT break it into individual words. The meaning of an idiom is not the sum of its parts.

For every entry produce:
1. normalized — the canonical form of the word or expression (verb → infinitive, noun → article + nominative singular e.g. ο άνδρας / η γυναίκα / το παιδί, idiom → its standard citation form)
2. translation — Russian translation of the word or expression as a whole
3. original — the form as it appears in the image (use the same value as normalized when identical)

Focus on meaningful vocabulary: nouns, verbs, adjectives, adverbs, conjunctions, particles, idioms, and set phrases. Skip standalone punctuation and bare numerals.
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
