"""Classify a plant species into a sprite archetype + color palette via the
Anthropic API, so procedural sprites look species-appropriate rather than
randomly colored. Falls back to a neutral default if the API key is missing
or the call fails, so the app still works offline (per CLAUDE.md).
"""
import os

from pydantic import BaseModel

ARCHETYPES = (
    "tree", "bush", "variant_tree", "variant_bush",
    "flower_rose", "flower_tulip", "flower_daisy", "flower_orchid",
    "fern", "sapling",
)

NEUTRAL_ARCHETYPE = "bush"
NEUTRAL_PALETTE = ["#4a8f3c", "#6fb84f", "#2f5e28"]


class ArchetypeResult:
    def __init__(self, archetype, palette, fallback_used=False):
        self.archetype = archetype
        self.palette = palette
        self.fallback_used = fallback_used


class _Classification(BaseModel):
    archetype: str
    palette: list[str]


def _neutral_result():
    return ArchetypeResult(NEUTRAL_ARCHETYPE, NEUTRAL_PALETTE, fallback_used=True)


def classify_species(species):
    """Return an ArchetypeResult for the given species string.

    Requires ANTHROPIC_API_KEY in the environment. On any failure (missing
    key, network error, bad response), returns a neutral fallback rather
    than raising, so plant creation never blocks on network access.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return _neutral_result()

    try:
        import anthropic

        client = anthropic.Anthropic()
        response = client.messages.parse(
            model="claude-opus-4-8",
            max_tokens=256,
            output_config={"effort": "low"},
            messages=[{
                "role": "user",
                "content": (
                    f"Classify the garden plant species \"{species}\" for a "
                    "pixel-art sprite generator. Choose exactly one archetype "
                    f"from this list: {', '.join(ARCHETYPES)}. Also give a "
                    "3-5 color hex palette (leaf/flower colors typical of "
                    "this species in real life)."
                ),
            }],
            output_format=_Classification,
        )
        result = response.parsed_output
        if result.archetype not in ARCHETYPES or not result.palette:
            return _neutral_result()
        return ArchetypeResult(result.archetype, result.palette, fallback_used=False)
    except Exception:
        return _neutral_result()
