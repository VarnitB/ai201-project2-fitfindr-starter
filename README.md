# FitFindr

## 1. Project Overview

FitFindr is a multi-tool AI agent for secondhand fashion. A user describes what they want to thrift (for example, *"vintage graphic tee under $30"*), and the app:

1. Searches a mock listings dataset for matching items
2. Suggests how to style the top result with the user's wardrobe
3. Generates a short, shareable fit card caption

The agent is built around three tools orchestrated by a planning loop in `agent.py`, with a Gradio UI in `app.py`. LLM-powered styling and captions use Groq (`llama-3.3-70b-versatile`).

---

## 2. Setup and Run Instructions

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root with your Groq API key (free at [console.groq.com](https://console.groq.com)):

```
GROQ_API_KEY=your_key_here
```

Run the app:

```bash
python app.py
```

Open the localhost URL shown in the terminal (usually `http://localhost:7860`). Try a happy-path query such as **vintage graphic tee under $30** with **Example wardrobe** selected. All three output panels should populate: top listing, outfit idea, and fit card.

Run tests:

```bash
pytest tests/ -v
```

---

## 3. Tool Inventory

### `search_listings`

**Signature:** `search_listings(description: str, size: str | None = None, max_price: float | None = None) -> list[dict]`

| Input | Type | Purpose |
|-------|------|---------|
| `description` | `str` | Item/style keywords to match (e.g. `"vintage graphic tee"`) |
| `size` | `str \| None` | Optional size filter; case-insensitive substring match (e.g. `"M"` matches `"S/M"`) |
| `max_price` | `float \| None` | Optional maximum price (inclusive) |

**Output:** `list[dict]` — matching listings from `data/listings.json`, sorted by relevance (best first). Each dict contains: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, `platform`. Returns `[]` when nothing matches.

**Purpose:** Filter and rank mock secondhand listings by description keywords, optional size, and optional budget.

---

### `suggest_outfit`

**Signature:** `suggest_outfit(new_item: dict, wardrobe: dict) -> str`

| Input | Type | Purpose |
|-------|------|---------|
| `new_item` | `dict` | Selected listing dict from `search_listings` |
| `wardrobe` | `dict` | User wardrobe with `wardrobe["items"]` — each item has `id`, `name`, `category`, `colors`, `style_tags`, `notes` |

**Output:** `str` — non-empty outfit recommendation. With wardrobe items, suggests 1–2 combos using named pieces. With an empty wardrobe, returns general styling advice.

**Purpose:** Use Groq to recommend how to wear the thrifted item with pieces the user already owns (or general advice if the wardrobe is empty).

---

### `create_fit_card`

**Signature:** `create_fit_card(outfit: str, new_item: dict) -> str`

| Input | Type | Purpose |
|-------|------|---------|
| `outfit` | `str` | Outfit suggestion string from `suggest_outfit` |
| `new_item` | `dict` | Selected listing dict |

**Output:** `str` — short OOTD-style caption (1–3 sentences), or a clear error/fallback string if input is invalid or the LLM call fails.

**Purpose:** Turn the outfit suggestion into a casual, shareable fit card caption mentioning the item, price, and platform.

---

## 4. Planning Loop Explanation

`run_agent(query, wardrobe)` in `agent.py` implements conditional logic — it does **not** blindly call all three tools on every request.

1. **Initialize session** — `_new_session()` creates a session dict with `query`, `parsed`, `search_results`, `selected_item`, `wardrobe`, `outfit_suggestion`, `fit_card`, and `error`.

2. **Parse query** — rule-based regex extracts `description`, `size`, and `max_price` from phrases like `"under $30"` and `"size M"`, stored in `session["parsed"]`.

3. **Search** — calls `search_listings(description, size, max_price)` and stores the result in `session["search_results"]`.

4. **Branch on search results**
   - **If `search_results` is empty:** set `session["error"]` to a helpful message, return session immediately. `selected_item`, `outfit_suggestion`, and `fit_card` stay `None`. **`suggest_outfit` and `create_fit_card` are not called.**
   - **If results exist:** set `session["selected_item"] = search_results[0]` (top match).

5. **Style** — call `suggest_outfit(selected_item, wardrobe)` → store in `session["outfit_suggestion"]`.

6. **Caption** — call `create_fit_card(outfit_suggestion, selected_item)` → store in `session["fit_card"]`.

7. **Return session** — `app.py` maps the session to the three Gradio output panels.

---

## 5. State Management

The session dict is the single source of truth for one user interaction.

| Field | When set | Role |
|-------|----------|------|
| `query` | Session init | Original user request |
| `parsed` | After query parsing | `{description, size, max_price}` passed to `search_listings` |
| `search_results` | After search | Full list of matching listing dicts |
| `selected_item` | After successful search | Top listing (`search_results[0]`) passed to `suggest_outfit` and `create_fit_card` |
| `wardrobe` | Session init | User wardrobe passed into `suggest_outfit` |
| `outfit_suggestion` | After `suggest_outfit` | String passed to `create_fit_card` as `outfit` |
| `fit_card` | After `create_fit_card` | Final caption shown in the UI |
| `error` | On no search results | Early-termination message; downstream fields remain `None` |

**Data flow:** `parsed` → `search_listings` → `search_results` → `selected_item` → `suggest_outfit` → `outfit_suggestion` → `create_fit_card` → `fit_card`.

The same `selected_item` dict flows from search through styling to the fit card, so the UI always reflects one consistent listing.

---

## 6. Error Handling Strategy

| Tool | Failure mode | Behavior |
|------|--------------|----------|
| `search_listings` | No matches | Returns `[]` without raising |
| `run_agent` | Empty search results | Sets `session["error"]`, returns early; does not call later tools |
| `suggest_outfit` | Empty wardrobe | Returns general styling advice (Groq or fallback string) |
| `create_fit_card` | Empty outfit input | Returns `"I need an outfit suggestion before I can create a fit card."` |

### Concrete examples from testing

**Full agent — no results (Milestone 5):**

Query: `designer ballgown size XXS under $5`

- `session["error"]`: *I couldn't find any listings that matched your search. Try broadening the description, removing the size filter, or increasing the max price.*
- `selected_item`, `outfit_suggestion`, `fit_card`: all `None`

This confirms the agent stops after search failure and does not generate outfit or fit card content.

**`create_fit_card` — empty outfit (Milestone 5):**

Calling `create_fit_card("", item)` returned:

> I need an outfit suggestion before I can create a fit card.

No exception was raised; the tool returned a clear descriptive message instead of generating a caption from missing data.

---

## 7. Testing

Run:

```bash
pytest tests/ -v
```

**Result:** 6 tests passed.

| Test | What it covers |
|------|----------------|
| `test_search_returns_results` | Normal search returns a non-empty list of dicts |
| `test_search_empty_results` | Impossible query returns `[]` |
| `test_search_price_filter` | All results respect `max_price` |
| `test_suggest_outfit_empty_wardrobe` | Returns non-empty string with empty wardrobe |
| `test_create_fit_card_empty_outfit` | Returns error string containing "outfit" or "suggestion" |
| `test_create_fit_card_normal_input` | Returns non-empty string for valid outfit input |

LLM tests assert type and non-empty output only — not exact wording — so they remain stable across Groq responses.

---

## 8. Spec Reflection

**How planning helped:** The tool specs and architecture diagram in `planning.md` made it clear that the no-results search branch should stop early before outfit generation. That prevented wiring `suggest_outfit` and `create_fit_card` to run on empty search data.

**Where implementation diverged:** Early drafts in `planning.md` described `description`, `size`, and `max_price` as top-level session keys. The final agent stores them inside `session["parsed"]` instead, matching the starter repo's `_new_session()` structure in `agent.py`. This kept the implementation aligned with the provided session template without changing the overall flow.

---

## 9. AI Usage

1. **Tool 1 — `search_listings`:** Used Cursor with the Tool 1 spec from `planning.md` to generate the implementation. I revised and verified that it calls `load_listings()` (not raw JSON loading), handles `size=None` and `max_price=None`, scores keyword matches across listing fields, and returns `[]` on no results without crashing.

2. **Planning loop — `run_agent`:** Used Cursor with the Planning Loop, State Management, and Architecture sections to implement `run_agent()`. I verified it branches on empty `search_results`, sets `session["error"]`, and does **not** call `suggest_outfit` or `create_fit_card` when search fails.

3. **Pytest setup:** Used Cursor to create `tests/test_tools.py`. I revised the import path by adding a `sys.path` setup so pytest could import `tools.py` from the repo root when tests are run with `pytest tests/ -v`.

---

## 10. Demo Video

Demo video: https://youtu.be/rHnzEnTHVX8 

---

## Project Structure

```
ai201-project2-fitfindr-starter/
├── agent.py              # Planning loop (run_agent)
├── app.py                # Gradio UI
├── tools.py              # search_listings, suggest_outfit, create_fit_card
├── planning.md           # Design spec
├── data/
│   ├── listings.json     # 40 mock secondhand listings
│   └── wardrobe_schema.json
├── utils/
│   └── data_loader.py
├── notes/
│   └── milestone5_failure_tests.txt
├── tests/
│   └── test_tools.py
└── requirements.txt
```
