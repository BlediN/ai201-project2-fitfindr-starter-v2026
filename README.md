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
  - **Score, revised in unit 4:** each keyword found in the listing adds its *weight*, doubled if the keyword is in the `title`. A keyword's weight is `log(1 + N / n)`, where N is the number of listings and n is how many of them contain the word, so rare words like "silk" count more than common ones like "vintage". Weights are counted over all listings, before any filtering. Listings that score 0 are still dropped, and ties still keep file order.
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
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The same item reaches every tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card: 2–4 sentences, price, platform; no shared opening | 4 of 5, and no shared opening | PASS | PASS | PASS | PASS | PASS | MET (5/5, 5 distinct openings) |
| 5. The empty wardrobe completes | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Full log: `results/run_2026-10-12_2309_before.md`. For criterion 4, Try 1–5
are five **different items**: slip dress, platform sneakers, track jacket,
knit cardigan, linen blazer. I used the Try 1 card of each, because the
criterion is about five cards for five items. Scored on its own, every one of
the 25 cards those scenarios produced also passes.

**Real output from one try**, pasted as text, naming the file and function
that produced it. Criterion 3, try 1, produced by `agent.py::run_agent` and
logged by `run_eval.py::main`:

```
query: jeans size W30 under $40   (example wardrobe)

[1] parse_query
      in:  jeans size W30 under $40
      out: description='jeans', size='W30', max_price=40.0
[2] search_listings (via MCP)
      in:  description='jeans', size='W30', max_price=40.0
      out: 1 items: Vintage Levi's 501 Jeans — Medium Wash
      →    branch: selected Vintage Levi's 501 Jeans — Medium Wash [lst_001]
[3] suggest_outfit
      in:  new_item=Vintage Levi's 501 Jeans — Medium Wash [lst_001], wardrobe=10 items
      out: Outfit 1: Pair the Vintage Levi's 501 Jeans with the White ribbed tank top, the Vintage black denim jacket, an…
[4] create_fit_card
      in:  outfit=<328 chars>, new_item=Vintage Levi's 501 Jeans — Medium Wash [lst_001]
      out: Nothing beats the way 501s actually mold to you once they're properly broken in. These medium wash gems have t…

Fit card: Nothing beats the way 501s actually mold to you once they're properly broken in. These medium wash gems have that effortless 90s off-duty model vibe, especially paired with an oversized crewneck and chunky boots. Grab them for $38 over on my depop before I change my mind and keep them. 👖✨
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
| 1 | A matching query completes all three tools | 4 of 5 | **MET** (5/5) | All 5 traces show four steps and a non-empty `fit_card`. |
| 2 | An impossible query stops before the second tool | 5 of 5 | **MET** (5/5) | All 5 traces end after `search_listings`, `fit_card` is `None`, and the message tells the user to use a more general word. |
| 3 | The same item reaches every tool | 5 of 5 | **MET** (5/5) | `lst_001` appears in the search branch note, the `suggest_outfit` input and the `create_fit_card` input in all 5 traces. |
| 4 | Fit card: 2–4 sentences, price, platform; no shared opening | 4 of 5, no shared opening | **MET** (5/5) | I read the Try 1 card of each of the 5 items: all are 2–4 sentences with the exact price and the platform, and the 5 opening sentences are all different. All 25 cards also pass when scored one by one. |
| 5 | The empty wardrobe completes | 5 of 5 | **MET** (5/5) | All 5 runs ended with `error` as `None` and a non-empty suggestion and card. |

**Diagnoses**

**I missed nothing: 25 of 25 tries passed.** Honestly, that says more about my targets than my agent. Three of the five (2, 3, 5) test code paths with no model in them, so they were always going to be 5 of 5 once the code was right. The run output shows problems that none of my criteria catch.

**The criterion I'd tighten is 1, and it's broken, not just easy.** It passed 5 of 5 while the agent picked the **wrong item in every try**. The query was "vintage graphic tee", and all five runs selected `lst_002` "Y2K Baby Tee — Butterfly Print", not `lst_006` "Graphic Tee — 2003 Tour Bootleg Style". The criterion checks that the run *finishes*, and a run that confidently finds the wrong thing still finishes. I revised it in `criteria.md`; the original line is still there. The new version checks whether the agent picked the right listing, for 5 queries that each have one correct answer.

**Scored against the revised criterion 1, the agent misses: 3 of 5.** The selected item depends only on `parse_query` and `search_listings`, with no model involved, so the same query gives the same pick every time and running it once gives the result for all five tries.

| Query | Should pick | Picked | Result |
|---|---|---|---|
| `vintage graphic tee under $30` | `lst_006` Graphic Tee — 2003 Tour Bootleg Style | `lst_002` Y2K Baby Tee — Butterfly Print | MISS |
| `leather jacket` | `lst_022` 90s Leather Bomber — Black | `lst_022` | PASS |
| `black jeans size W28` | `lst_037` Straight Leg Black Jeans — Faded | `lst_037` | PASS |
| `green silk shirt` | `lst_029` Silk Button-Down — Sage Green | `lst_013` 90s Silk Slip Dress — Floral | MISS |
| `canvas sneakers` | `lst_035` Low-Top Canvas Sneakers — Off-White | `lst_035` | PASS |

**Diagnosis: one problem in one tool, `search_listings`, at the scoring step.** The score counts how many query words appear *anywhere* in the listing's text. Every match counts the same, whether it's in the title or buried in the description. So the item the user named and a weaker match end up tied, and `sorted()` breaks ties by file order:
- `vintage graphic tee`: both tees score **3/3**. The baby tee only has "graphic" because its description says "butterfly graphic", and "vintage" because it's a style tag. `lst_002` comes before `lst_006` in the file, so it wins.
- `green silk shirt`: both score **2/3** (green, silk). Neither says "shirt", because the right item is titled "Button-Down". `lst_013` comes first, so a dress wins over the shirt.

The loop, the session and the model all did their jobs. They faithfully carried the wrong item forward, which is exactly what criterion 3 says they should do.

**The same mechanism also breaks the empty-search branch.** `wool trench coat` should stop, because there's no coat in the data. Instead it selects `lst_003` "Oversized Flannel Shirt", because the word "wool" appears in its text and **1 match out of 3 is enough** to pass the zero-score filter. The branch only fires when *nothing* matches at all, so a query with one stray match skips it and the run carries on with an unrelated item. That's the same tool with the same weakness: no difference between a strong match and a weak one.

**Two model-output problems no criterion measures yet.** Of the 40 fit cards in the run, **18 are written as the seller** ("grab it before I change my mind and keep it", "listing it on my Poshmark"), and **10 open with "Nothing beats…"**. Criterion 4 passes as written because no two cards share a *whole* opening sentence, but the model leans on one template. If I tightened a second criterion, it would be 4, to compare opening words instead of whole sentences.


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
$ python app.py ask 'vintage graphic tee under $30' --trace
[1] parse_query
      in:  vintage graphic tee under $30
      out: description='vintage graphic tee', size=None, max_price=30.0
[2] search_listings (via MCP)
      in:  description='vintage graphic tee', size=None, max_price=30.0
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    branch: selected Y2K Baby Tee — Butterfly Print [lst_002]
[3] suggest_outfit
      in:  new_item=Y2K Baby Tee — Butterfly Print [lst_002], wardrobe=10 items
      out: Outfit 1: Pair the Y2K Baby Tee with the baggy straight-leg jeans, dark wash, vintage black denim jacket, and …
[4] create_fit_card
      in:  outfit=<243 chars>, new_item=Y2K Baby Tee — Butterfly Print [lst_002]
      out: That little butterfly graphic takes me straight back to 2003 in the best way possible. I love how it balances …
```

**Empty search**

```
$ python app.py ask 'designer ballgown size XXS under $5' --trace
[1] parse_query
      in:  designer ballgown size XXS under $5
      out: description='designer ballgown', size='XXS', max_price=5.0
[2] search_listings (via MCP)
      in:  description='designer ballgown', size='XXS', max_price=5.0
      out: [] (empty)
      →    branch: empty, stopping before suggest_outfit
```

The empty search stops after step 2. The happy path runs all four steps, and the same item id, `lst_002`, appears in the branch note and in the inputs to both `suggest_outfit` and `create_fit_card`.

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:** The scoring step inside `tools.py::search_listings`, and nothing else. Before, a listing scored 1 point for every query word found anywhere in its text. Now each matched word is worth more when it's **rare** across the listings (`_keyword_weights`, weight `log(1 + N / n)`), and **double** when it's in the title. The loop, the session, the prompts and the empty-search branch are all unchanged.

**Which failure it was meant to fix:** Revised criterion 1, which scored 3 of 5 because the search picked the wrong listing for "vintage graphic tee" and "green silk shirt". The diagnosis traced both misses to one mechanism. Every match counted the same, so the listing the user named tied with one that only *mentioned* the words ("butterfly graphic" in a description, "vintage" as a style tag), and file order broke the tie. Title weighting alone fixed the tee but still lost "green silk shirt" to a green *polo shirt* in another tie. Weighting by rarity is what separates them: "silk" is in 2 listings and "shirt" is in many.

Before running the eval, I checked the change on the search alone, through the same MCP path the agent uses:
- All 5 revised criterion 1 queries now pick the correct listing.
- All 8 other scenario queries still pick the same item as before.
- The impossible query still returns `[]`.

**Deliberately not fixed:** `wool trench coat` still selects the flannel shirt, because one stray word match is enough to get past the branch. That's a different problem: a second branch, or a minimum score, would fix it. I left it alone so this run measures one change.

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. (revised) The right listing is selected | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The same item reaches every tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card: 2–4 sentences, price, platform; no shared opening | 4 of 5, and no shared opening | PASS | PASS | PASS | PASS | PASS | MET (5/5, 5 distinct openings) |
| 5. The empty wardrobe completes | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Full log: `results/run_2026-10-12_2341_after.md`. For criterion 1, Try 1–5
are the five revised queries, and every one of their 25 tries picked the
expected id. For criterion 4, Try 1–5 are the five items, as in the before
run.

### Before and after, side by side

| Criterion | Before (`run_2026-10-12_2309_before.md`) | After (`run_2026-10-12_2341_after.md`) | Changed? |
|---|---|---|---|
| 1. A matching query completes (original) | MET 5/5, but picked the wrong tee every time | MET 25/25 | — |
| 1. The right listing is selected (revised) | **MISSED 3/5**: graphic tee → baby tee, green silk shirt → slip dress | **MET 5/5**, all five correct | **Yes, fixed** |
| 2. An impossible query stops early | MET 5/5 | MET 5/5 | No |
| 3. The same item reaches every tool | MET 5/5 (`lst_001`) | MET 5/5 (`lst_001`) | No |
| 4. Fit card | MET 5/5 | MET 5/5 | No |
| 5. The empty wardrobe completes | MET 5/5 | MET 5/5 | No |

**Where the "before 3/5" for revised criterion 1 comes from.** The before run
didn't contain those five queries, because I wrote the revised criterion
after it. I scored them on the unchanged code by calling
`parse_query` → `search_listings` directly. That's a fair stand-in: which
item gets picked doesn't involve the model, so every try gives the same
answer. The after run confirms that, with the same pick in all 5 tries of each
query.

**Did it help, and how do I know:**

**Yes, for what it targeted.** Revised criterion 1 went from **3 of 5
(MISSED) to 5 of 5 (MET)**. Both misses are fixed, and you can see it in the
trace's branch note:
- `vintage graphic tee under $30` now selects `lst_006` "Graphic Tee — 2003 Tour Bootleg Style" (was `lst_002`, the baby tee).
- `green silk shirt` now selects `lst_029` "Silk Button-Down — Sage Green" (was `lst_013`, a slip dress).

**Nothing else got worse.** Criteria 2–5 are still 5 of 5. The criterion 3 and
4 scenarios and the empty-wardrobe scenario selected the same listings as in
the before run: `lst_001`, `lst_013`, `lst_019`, `lst_004`, `lst_008`,
`lst_018` and `lst_007`. The impossible query still returns `[]` and stops.

**What it didn't fix, and wasn't meant to:**
- `wool trench coat` still selects the flannel shirt. One stray word match still gets a run past the empty-search branch. Better scoring makes the *order* right, but it can't make an irrelevant result disappear. That needs a second branch or a minimum score.
- The fit cards are no better. Seller voice is in 32 of 60 cards (53%, was 18 of 40, 45%), and "Nothing beats…" openings are in 14 of 60 (23%, was 10 of 40, 25%). The small changes are run-to-run variation in the model, not an effect of my change. Three of criterion 4's five Try 1 cards begin "Nothing beats", which passes the criterion's "no shared opening *sentence*" but shows the template. No prompt changed, so this is expected, and it's the next thing I'd fix.

**One honest caveat about the improvement.** The weights come from these 40
listings. "Silk" is rare *here*. With a different catalogue, the same query
could rank differently. The fix makes the search reward distinctive words in
the title, which is the right idea in general, but I've only measured it on
this data.


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
