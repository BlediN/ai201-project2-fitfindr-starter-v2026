# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->

FitFindr helps someone shop secondhand clothing listings (Depop, thredUp and Poshmark) in plain language. You type something like `vintage graphic tee under $30, size M`. The agent pulls out a description, a size and a price ceiling, then searches the listings for the best match. If it finds one, it suggests one or two outfits built from pieces you already own, or general styling ideas if your wardrobe is empty, and writes a short caption you could post about the find. If nothing matches, it stops before the outfit step and tells you which part of your request to change: the words, the size, or the price.


---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Filters `data/listings.json` by price and size, then ranks what's left by how many of the description's keywords it contains. It does not call the model.
- **Inputs:**
  - `description` (str): keywords for what the user wants, e.g. `"vintage graphic tee"`.
  - `size` (str or None): the size to filter by. `None` skips size filtering.
  - `max_price` (float or None): the price ceiling, inclusive (`price <= max_price`). `None` skips price filtering.
- **Returns:** A `list[dict]` of at most `config.SEARCH_RESULT_LIMIT` (10) listing dicts, highest score first. Ties keep the order they have in the file. Each dict is the full listing, unchanged: `id` (str), `title` (str), `description` (str), `category` (str), `style_tags` (list of str), `size` (str), `condition` (str), `price` (float), `colors` (list of str), `brand` (str or None, and usually None), `platform` (str).
  - **Score:** lowercase the description and split it on whitespace into keywords. A listing's score is the number of those keywords found in its combined `title`, `description`, `category`, `style_tags`, `colors` and `brand` (lowercased). Listings that score 0 are dropped.
  - **Size match:** lowercase both sizes, delete anything in parentheses from the listing's size, and split it on `/` into parts, stripping the spaces around each part. It matches if the requested size equals a whole part, or equals the first word of a part. Listings sized `one size` match every request. So `M` matches `S/M` and `M/L`; `L` matches `L/XL` but not `XL`; `W30` matches `W30 L30`; `S` does **not** match `US 9`; `US 8` does **not** match `US 8.5`.
- **When it has nothing:** It returns an empty list `[]`. Never `None`, and never an exception.

### `suggest_outfit`

- **What it does:** Asks the model, through `generate()`, for one or two outfits built around the item.
- **Inputs:**
  - `new_item` (dict): one listing dict, in the shape `search_listings` returns.
  - `wardrobe` (dict): a wardrobe with an `items` key holding a list of wardrobe item dicts (see `data/wardrobe_schema.json`). The list may be empty.
- **Returns:** A non-empty `str` with one or two outfit suggestions. When the wardrobe has items, each outfit names specific pieces from `wardrobe["items"]`.
- **When it has nothing:** If `wardrobe["items"]` is empty, it still returns a non-empty `str`: general styling advice for the item that doesn't mention owned pieces. It never returns `""` and never raises.

### `create_fit_card`

- **What it does:** Asks the model, through `generate()`, for a short caption someone would post about the find.
- **Inputs:**
  - `outfit` (str): the string `suggest_outfit` returned.
  - `new_item` (dict): the listing dict for the item.
- **Returns:** A `str` caption of 2–4 sentences that reads like a social post, not a product description. It mentions the item's `title`, `price` and `platform` once each and is specific about the vibe. Output varies between runs (`TEMPERATURE = 0.9`), but only when the cache is off (`AI201_CACHE=0`).
- **When it has nothing:** If `outfit` is empty or only whitespace, it doesn't call the model. It returns the fixed message `"Can't write a fit card without an outfit suggestion."` and never raises.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, set `session["error"]` to a message that tells the user what to change (raise the price limit, drop or change the size, or use broader keywords), return the session, and don't call `suggest_outfit`. Otherwise, put the first result in `session["selected_item"]` and pass it, with the wardrobe, to `suggest_outfit`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** By regex, in `agent.py::parse_query`, with no model call.
- **Price:** a `$` amount, optionally after "under", "below", "up to" and similar words (`under $30` → `30.0`), or a bare number after one of those words (`under 40`).
- **Size:** the word after "size" (`size M` → `M`, `size W30` → `W30`). A bare number of 15 or less becomes a US shoe size (`size 8` → `US 8`), because that's how the shoes in the data are sized.
- **Description:** what's left after the price and size are removed, minus filler words like "a", "in", "looking" and "for". Removing filler matters because `search_listings` matches substrings, so "a" would match every listing.

**What moves through the session:** in this order:
1. `query`, the raw text, set by `new_session`.
2. `parsed`: `description`, `size`, `max_price`.
3. `search_results`: the list `search_listings` returned.
4. Then the branch. On an empty list, `error` is set and the run stops, leaving `selected_item`, `outfit_suggestion` and `fit_card` as `None`. Otherwise:
5. `selected_item`, which is `search_results[0]`.
6. `outfit_suggestion`, built from `selected_item` and `wardrobe`.
7. `fit_card`, built from `outfit_suggestion` and `selected_item`.

Each tool reads its inputs back out of the session, never from the previous call's return value.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'
  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Outfit 1:
Pair the Y2K Baby Tee with the baggy straight-leg jeans, dark wash, vintage black denim jacket, and chunky white sneakers.

Outfit 2:
Pair the Y2K Baby Tee with the wide-leg khaki trousers, brown leather belt, and black combat boots.

  Fit card: That little butterfly graphic takes me straight back to 2003 in the best way possible. I love how it balances out with oversized dark denim and chunky sneakers for an effortless off-duty look, but it’s just as cute tucked into baggy trousers with combat boots. Snagged this baby tee on depop for $18 and I'm obsessed 🦋
```

And one the data can't match, which stops at the branch:

```
$ python app.py ask 'denim jacket size M under $5'
  Nothing matched 'denim jacket' in size M under $5. There are listings for 'denim jacket', but not with those filters — try to raise the price limit above $5 or drop the size M.
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print([(l['title'], l['price']) for l in search_listings('graphic tee', max_price=30)])"
[('Y2K Baby Tee — Butterfly Print', 18.0), ('Graphic Tee — 2003 Tour Bootleg Style', 24.0), ('Mesh Long-Sleeve Top — Black', 15.0), ('Vintage Band Tee — Faded Grey', 19.0), ('Low-Rise Cargo Pants — Khaki', 27.0), ('Oversized Crewneck Sweatshirt — Vintage Navy', 20.0), ('Vintage Graphic Hoodie — Faded Black', 26.0)]

$ python -c "from tools import search_listings; print(search_listings('designer ballgown', size='XXS', max_price=5))"
[]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
Outfit 1
Pair the vintage Levi's 501 jeans with the white ribbed tank top, the vintage black denim jacket, and the chunky white sneakers. Add the black crossbody bag to finish the look.

Outfit 2
Pair the vintage Levi's 501 jeans with the oversized grey crewneck sweatshirt, the brown leather belt, and the black combat boots.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
These broken-in vintage Levi's 501 jeans have that perfect authentic fade you can't fake. I love throwing them on with crisp white sneakers for that effortless off-duty model look. Grab this pair for $38 over on my Depop before I change my mind. 👖✨
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* I asked Claude to fill in the Tool Inventory from the stubs in `tools.py`, including the size-matching rule the `search_listings` docstring says I have to decide for myself.
- *What came back:* Before writing the rule, it counted the actual size values in `listings.json` (`S/M`, `W30 L30`, `US 8.5`, `XL (oversized)`, `One Size (adjustable)` and others). It wrote a rule with worked examples: split on `/`, ignore notes in parentheses, and match a whole part or a part's first word. That way `M` matches `S/M` but `S` doesn't match `US 9`. The first draft of the `create_fit_card` spec also said captions "vary between runs" because `TEMPERATURE = 0.9`.
- *What I changed:* The "vary between runs" line was wrong. `CACHE_ENABLED` is on by default, so the same input returns the cached caption. The spec now says captions vary only with `AI201_CACHE=0`, and criterion 4 says the cache is off when it's measured. I also decided that "One Size" listings match every size request, and I wrote that into the rule.

**Moment 2**

- *What I asked for:* I asked Claude to build `search_listings` to my spec and test it, then wire the loop in `run_agent` with a regex query parser.
- *What came back:* The search passed every filter test: price ceiling, `[]` for the ballgown query, and no `US 9` for size `S`. But "graphic tee" also returned cargo pants and a plain crewneck. My spec matches keywords as substrings, so "graphic" matched "no graphics" and "tee" matched a description that mentions "a long tee". When it wired the loop, the same substring rule meant any leftover filler word in the parsed description, like "a", "in" or "for", would match every listing and make the empty-search branch impossible to reach.
- *What I changed:* I added a filler-word list to `parse_query` so the description that reaches the search holds only real keywords ("looking for a vintage graphic tee under $30" → `vintage graphic tee`). I kept substring matching for now because it's what my spec says. The bad ranking is real, though: the top result for "vintage graphic tee" is a butterfly baby tee, not the graphic tee. I'm leaving it as a known weakness to diagnose in unit 4.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
