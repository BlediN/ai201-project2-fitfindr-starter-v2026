"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable
from mcp_client import call_tool


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)

    # Each pass runs one step, then picks the next step from what that step
    # put in the session. Every tool reads its inputs back out of the session.
    next_step = "parse"
    count = 0
    while next_step != "done":
        count += 1
        trace.check_iterations(count)

        if next_step == "parse":
            session["parsed"] = parse_query(session["query"])
            next_step = "search"

        elif next_step == "search":
            parsed = session["parsed"]
            # Over MCP: same inputs, same list[dict] back as the direct call.
            session["search_results"] = call_tool("search_listings", {
                "description": parsed["description"],
                "size": parsed["size"],
                "max_price": parsed["max_price"],
            })
            # THE BRANCH: nothing found → explain what to change, and stop.
            if not session["search_results"]:
                session["error"] = _no_results_message(parsed)
                next_step = "done"
            else:
                session["selected_item"] = session["search_results"][0]
                next_step = "suggest"

        elif next_step == "suggest":
            session["outfit_suggestion"] = suggest_outfit(
                session["selected_item"], session["wardrobe"]
            )
            next_step = "card"

        elif next_step == "card":
            session["fit_card"] = create_fit_card(
                session["outfit_suggestion"], session["selected_item"]
            )
            next_step = "done"

    return session


# ── query parsing ─────────────────────────────────────────────────────────────

# Words that carry no meaning for search. They matter more than they look:
# search_listings matches keywords as substrings, so "a" or "in" left in the
# description would match every listing.
_FILLER = {
    "a", "an", "the", "i", "im", "i'm", "me", "my", "for", "in", "on", "of",
    "with", "and", "or", "to", "some", "something", "any", "looking", "want",
    "need", "find", "get", "show", "please", "like", "that", "is", "it",
}

_PRICE = re.compile(
    r"(?:under|below|less than|max|up to|at most|<)?\s*\$\s*(\d+(?:\.\d+)?)"
    r"|(?:under|below|less than|up to|at most)\s+(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
_SIZE = re.compile(
    r"\bsize\s+(us\s*\d+(?:\.\d+)?|w\d+(?:\s*l\d+)?|one size|[a-z0-9.]+)",
    re.IGNORECASE,
)


def parse_query(query: str) -> dict:
    """
    Pull a description, a size and a max_price out of plain language, by regex.

        "vintage graphic tee under $30"  → {"description": "vintage graphic tee",
                                            "size": None, "max_price": 30.0}
        "platform sneakers size 8"       → {"description": "platform sneakers",
                                            "size": "US 8", "max_price": None}

    A bare number size of 15 or under is read as a US shoe size, because that
    is how the shoes in the data are sized ("US 8").
    """
    text = query

    max_price = None
    price_match = _PRICE.search(text)
    if price_match:
        max_price = float(price_match.group(1) or price_match.group(2))
        text = text[: price_match.start()] + " " + text[price_match.end():]

    size = None
    size_match = _SIZE.search(text)
    if size_match:
        size = size_match.group(1).strip()
        if re.fullmatch(r"\d+(\.\d+)?", size) and float(size) <= 15:
            size = f"US {size}"
        text = text[: size_match.start()] + " " + text[size_match.end():]

    words = re.findall(r"[a-z0-9'-]+", text.lower())
    description = " ".join(w for w in words if w not in _FILLER)

    return {"description": description, "size": size, "max_price": max_price}


def _no_results_message(parsed: dict) -> str:
    """
    Tell the user what to change, not just that nothing came back. Checks
    whether the words match anything at all with the filters removed, so the
    message can say which part of the query is the problem.
    """
    asked = f"'{parsed['description']}'"
    if parsed["size"]:
        asked += f" in size {parsed['size']}"
    if parsed["max_price"] is not None:
        asked += f" under ${parsed['max_price']:g}"

    if not parsed["description"] or not search_listings(parsed["description"]):
        return (
            f"Nothing matched {asked}. None of the listings mention those words "
            f"at all, so changing the size or price won't help. Try a more general "
            f"word for the item, like 'jacket', 'jeans', 'tee' or 'sneakers'."
        )

    fixes = []
    if parsed["max_price"] is not None:
        fixes.append(f"raise the price limit above ${parsed['max_price']:g}")
    if parsed["size"]:
        fixes.append(f"drop the size {parsed['size']}")
    return (
        f"Nothing matched {asked}. There are listings for "
        f"'{parsed['description']}', but not with those filters — try to "
        + " or ".join(fixes) + "."
    )


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
