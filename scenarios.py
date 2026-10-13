"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

Three scenarios are filled in to show the shape. Add or change whatever your
own criteria need — these are a starting point, not a fixed set.
"""

SCENARIOS = [
    {
        # A query the data can match. Criterion 1.
        "name": "matching query completes",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 1,
    },
    {
        # A query nothing can match. Criterion 2 — the branch.
        "name": "impossible query stops early",
        "query": "designer ballgown size XXS under $5",
        "wardrobe": "example",
        "criterion": 2,
    },
    {
        # Criterion 3 — state. A query that uses all three parsed fields, so a
        # size or price lost between steps would show. PASS when the trace shows
        # the same id in the search_listings branch note, the suggest_outfit
        # input and the create_fit_card input (expected: lst_001).
        "name": "same item reaches every tool",
        "query": "jeans size W30 under $40",
        "wardrobe": "example",
        "criterion": 3,
    },
    # Criterion 4 — the fit card, for 5 DIFFERENT items. The criterion is about
    # five cards for five items, so it's scored across these five scenarios:
    # in the README row, Try 1..5 = Try 1 of item 1..5. A card PASSES when it
    # is 2–4 sentences and has the exact price and the platform name. Then
    # check that no two of the five share an opening sentence.
    # The five cover all three platforms, branded and unbranded items, and
    # four categories.
    {
        # lst_013 — $30, depop, no brand, dress
        "name": "fit card: item 1 (slip dress)",
        "query": "silk slip dress under $40",
        "wardrobe": "example",
        "criterion": 4,
    },
    {
        # lst_019 — $48, poshmark, no brand, shoes
        "name": "fit card: item 2 (platform sneakers)",
        "query": "platform sneakers size 8",
        "wardrobe": "example",
        "criterion": 4,
    },
    {
        # lst_004 — $45, poshmark, Champion, outerwear
        "name": "fit card: item 3 (track jacket)",
        "query": "90s track jacket in size M",
        "wardrobe": "example",
        "criterion": 4,
    },
    {
        # lst_008 — $35, depop, no brand, knitwear
        "name": "fit card: item 4 (knit cardigan)",
        "query": "chunky knit cardigan",
        "wardrobe": "example",
        "criterion": 4,
    },
    {
        # lst_018 — $38, thredUp, no brand, outerwear
        "name": "fit card: item 5 (linen blazer)",
        "query": "linen blazer",
        "wardrobe": "example",
        "criterion": 4,
    },
    {
        # Criterion 5 — a user with nothing saved. One of unit 4's three
        # failure modes. PASS when error is None and both outfit_suggestion
        # and fit_card are non-empty.
        "name": "empty wardrobe completes",
        "query": "denim jacket under $50",
        "wardrobe": "empty",
        "criterion": 5,
    },
]

WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems
