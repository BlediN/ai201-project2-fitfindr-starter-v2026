"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    listings = load_listings()

    if max_price is not None:
        listings = [l for l in listings if l["price"] <= max_price]

    if size:
        listings = [l for l in listings if _size_matches(size, l["size"])]

    keywords = description.lower().split()
    scored = []
    for listing in listings:
        text = _searchable_text(listing)
        score = sum(1 for word in keywords if word in text)
        if score > 0:
            scored.append((score, listing))

    # sorted() is stable, so ties keep the order they have in the file.
    scored = sorted(scored, key=lambda pair: pair[0], reverse=True)
    return [listing for _, listing in scored[: config.SEARCH_RESULT_LIMIT]]


def _searchable_text(listing: dict) -> str:
    """Every field a keyword can match, lowercased into one string."""
    parts = [
        listing["title"],
        listing["description"],
        listing["category"],
        " ".join(listing["style_tags"]),
        " ".join(listing["colors"]),
        listing["brand"] or "",  # brand is None for most listings
    ]
    return " ".join(parts).lower()


def _size_matches(wanted: str, listing_size: str) -> bool:
    """
    The size rule from the Tool Inventory. Lowercase both, drop parenthesised
    notes, split the listing size on "/", and match a whole part or a part's
    first word. "One size" listings match every request.

        "M"  matches "S/M", "M/L"      "L"   does not match "XL"
        "W30" matches "W30 L30"        "S"   does not match "US 9"
    """
    wanted = " ".join(wanted.lower().split())
    cleaned = re.sub(r"\(.*?\)", "", listing_size.lower())
    parts = [" ".join(p.split()) for p in cleaned.split("/") if p.strip()]

    for part in parts:
        if part == "one size":
            return True
        if wanted == part or wanted == part.split()[0]:
            return True
    return False


def _price(listing: dict) -> str:
    """$24 rather than $24.0; $24.50 stays as it is."""
    return f"${listing['price']:.2f}".replace(".00", "")


def _describe(listing: dict) -> str:
    """The item, as a few lines the model can read."""
    lines = [
        f"Title: {listing['title']}",
        f"Category: {listing['category']}",
        f"Colors: {', '.join(listing['colors'])}",
        f"Style: {', '.join(listing['style_tags'])}",
        f"Condition: {listing['condition']}",
        f"Size: {listing['size']}",
    ]
    if listing["brand"]:
        lines.append(f"Brand: {listing['brand']}")
    return "\n".join(lines)


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    items = wardrobe.get("items") or []
    system = (
        "You are a stylist helping someone decide whether a thrifted piece "
        "works for them. Be concrete and brief. Plain text, no markdown headers."
    )

    if not items:
        prompt = (
            f"Here is a thrifted item:\n{_describe(new_item)}\n\n"
            "The user hasn't saved any wardrobe items. Suggest one or two outfits "
            "built around this item using common, easy-to-find pieces. Do not "
            "refer to anything as if the user already owns it."
        )
    else:
        owned = "\n".join(
            f"- {item['name']} ({item['category']}; {', '.join(item['colors'])})"
            for item in items
        )
        prompt = (
            f"Here is a thrifted item:\n{_describe(new_item)}\n\n"
            f"The user already owns:\n{owned}\n\n"
            "Suggest one or two outfits that pair this item with pieces from "
            "that list. Name each owned piece exactly as it's written above."
        )

    suggestion = generate(prompt, system=system).strip()
    # The spec promises a non-empty string, even if the model sends nothing.
    return suggestion or f"Style the {new_item['title']} with simple basics in neutral colors."


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    if not outfit or not outfit.strip():
        return "Can't write a fit card without an outfit suggestion."

    system = (
        "You write short social media captions about thrift finds. They sound "
        "like a real person posting, not a product listing."
    )
    prompt = (
        f"The find:\n{_describe(new_item)}\n"
        f"Price: {_price(new_item)}\n"
        f"Platform: {new_item['platform']}\n\n"
        f"How they're styling it:\n{outfit}\n\n"
        "Write a caption of 2 to 4 sentences. Mention the item, the price written "
        f"exactly as {_price(new_item)}, and the platform name, once each. Be "
        "specific about the vibe of this outfit. Open with something particular "
        "to this item, not a generic opener. Plain text, at most two emojis, "
        "no hashtags. Return only the caption."
    )
    return generate(prompt, system=system).strip()
