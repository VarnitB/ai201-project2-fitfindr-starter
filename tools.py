"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def _score_listing(listing: dict, keywords: list[str]) -> int:
    """Score a listing by keyword matches across searchable text fields."""
    if not keywords:
        return 0

    fields = [
        listing.get("title", "").lower(),
        listing.get("description", "").lower(),
        listing.get("category", "").lower(),
        " ".join(listing.get("style_tags", [])).lower(),
        " ".join(listing.get("colors", [])).lower(),
    ]
    brand = listing.get("brand")
    if brand:
        fields.append(brand.lower())

    score = 0
    for keyword in keywords:
        for field in fields:
            if keyword in field:
                score += 1
    return score


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    listings = load_listings()
    keywords = [word.lower() for word in description.split() if word.strip()]

    scored: list[tuple[int, dict]] = []
    for listing in listings:
        if max_price is not None and listing["price"] > max_price:
            continue
        if size is not None and size.lower() not in listing["size"].lower():
            continue

        score = _score_listing(listing, keywords)
        if score > 0:
            scored.append((score, listing))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [listing for _, listing in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

GROQ_MODEL = "llama-3.3-70b-versatile"


def _format_new_item(new_item: dict) -> str:
    """Format listing details for LLM prompts."""
    brand = new_item.get("brand") or "unknown brand"
    return (
        f"Title: {new_item.get('title', 'Unknown item')}\n"
        f"Category: {new_item.get('category', 'unknown')}\n"
        f"Colors: {', '.join(new_item.get('colors', [])) or 'unspecified'}\n"
        f"Style tags: {', '.join(new_item.get('style_tags', [])) or 'none'}\n"
        f"Price: ${new_item.get('price', 0):.2f}\n"
        f"Condition: {new_item.get('condition', 'unknown')}\n"
        f"Platform: {new_item.get('platform', 'unknown')}\n"
        f"Brand: {brand}\n"
        f"Description: {new_item.get('description', '')}"
    )


def _format_wardrobe_items(items: list[dict]) -> str:
    """Format wardrobe items for LLM prompts."""
    lines = []
    for item in items:
        notes = item.get("notes")
        notes_text = f"; notes: {notes}" if notes else ""
        lines.append(
            f"- {item.get('name', 'Unnamed item')} ({item.get('category', 'unknown')}): "
            f"colors {', '.join(item.get('colors', [])) or 'unspecified'}; "
            f"tags {', '.join(item.get('style_tags', [])) or 'none'}{notes_text}"
        )
    return "\n".join(lines)


def _fallback_outfit_suggestion(new_item: dict, wardrobe: dict) -> str:
    """Return readable styling advice when the LLM call fails."""
    title = new_item.get("title", "this item")
    category = new_item.get("category", "piece")
    style_tags = ", ".join(new_item.get("style_tags", [])) or "versatile"
    items = wardrobe.get("items") or []

    if items:
        named_pieces = [item.get("name", "a wardrobe piece") for item in items[:3]]
        pieces_text = ", ".join(named_pieces)
        return (
            f"Style {title} with pieces you already own. Try pairing it with {pieces_text}. "
            f"The {category} has a {style_tags} vibe, so lean into relaxed layers, "
            f"complementary colors, and one statement accessory to keep the look balanced."
        )

    return (
        f"Your wardrobe is empty, so here is general advice for {title}. "
        f"As a {category} with a {style_tags} feel, pair it with relaxed denim or neutral "
        f"bottoms, simple layers, and comfortable shoes that match the item's colors "
        f"({', '.join(new_item.get('colors', [])) or 'keep tones simple'})."
    )


def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    items = wardrobe.get("items") or []
    new_item_text = _format_new_item(new_item)

    if items:
        wardrobe_text = _format_wardrobe_items(items)
        user_prompt = (
            "Suggest 1-2 complete outfits using the thrifted item below with pieces "
            "from the user's existing wardrobe.\n\n"
            f"New thrifted item:\n{new_item_text}\n\n"
            f"User's wardrobe:\n{wardrobe_text}\n\n"
            "For each outfit:\n"
            "- Name the new item and specific wardrobe pieces by name\n"
            "- Mention optional layering if it helps\n"
            "- Briefly explain why the pieces work together\n"
            "Keep the response practical and concise."
        )
    else:
        user_prompt = (
            "The user's wardrobe is empty. Suggest how to style the thrifted item below "
            "using general styling advice.\n\n"
            f"New thrifted item:\n{new_item_text}\n\n"
            "Explain what kinds of bottoms, layers, shoes, and accessories would pair well, "
            "what vibe the outfit suits, and why those choices work."
        )

    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are FitFindr, a friendly secondhand fashion stylist. "
                        "Give specific, wearable outfit advice."
                    ),
                },
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )
        content = response.choices[0].message.content
        if content and content.strip():
            return content.strip()
    except Exception:
        pass

    return _fallback_outfit_suggestion(new_item, wardrobe)


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def _fallback_fit_card(outfit: str, new_item: dict) -> str:
    """Return a simple caption when the LLM call fails."""
    title = new_item.get("title", "this find")
    price = new_item.get("price", 0)
    platform = new_item.get("platform", "depop")
    style_tags = ", ".join(new_item.get("style_tags", [])[:2]) or "effortless"
    snippet = outfit.strip().split(".")[0][:80]
    return (
        f"thrifted {title.lower()} for ${price:.0f} on {platform} — "
        f"{style_tags} energy. {snippet}."
    )


def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    if not outfit or not outfit.strip():
        return "I need an outfit suggestion before I can create a fit card."

    title = new_item.get("title", "Unknown item")
    price = new_item.get("price", 0)
    platform = new_item.get("platform", "unknown")
    condition = new_item.get("condition", "unknown")
    colors = ", ".join(new_item.get("colors", [])) or "unspecified"
    style_tags = ", ".join(new_item.get("style_tags", [])) or "none"

    user_prompt = (
        "Write a short, casual OOTD caption for a thrift find and outfit combo.\n\n"
        f"Item title: {title}\n"
        f"Price: ${price:.2f}\n"
        f"Platform: {platform}\n"
        f"Condition: {condition}\n"
        f"Colors: {colors}\n"
        f"Style tags: {style_tags}\n\n"
        f"Outfit suggestion:\n{outfit.strip()}\n\n"
        "Requirements:\n"
        "- 1-3 sentences, Instagram/TikTok caption style\n"
        "- Sound natural and personal, not like a product listing\n"
        "- Mention the item, price, and platform once each in a casual way\n"
        "- Capture the outfit vibe in specific terms\n"
        "- No hashtags unless they feel natural"
    )

    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are FitFindr, writing short shareable outfit captions "
                        "for secondhand fashion finds."
                    ),
                },
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.85,
        )
        content = response.choices[0].message.content
        if content and content.strip():
            return content.strip()
    except Exception:
        pass

    return _fallback_fit_card(outfit, new_item)
