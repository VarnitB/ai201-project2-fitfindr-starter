# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
`search_listings` searches the mock secondhand listings dataset for items that match the user's requested item description, optional size, and maximum price. It filters listings using fields like title, description, category, style_tags, size, price, colors, brand, condition, and platform, then returns the best matching items.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): The clothing item or style the user is searching for, such as `"vintage graphic tee"` or `"black denim jacket"`.
- `size` (str or None): The requested size, such as `"S"`, `"M"`, `"L"`, or `None` if the user did not specify a size.
- `max_price` (float or None): The user's maximum budget, such as `30.0`, or `None` if the user did not give a price limit.

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
A list of listing dictionaries. Each dictionary represents one matching listing from `data/listings.json` and includes fields such as:
- `id` (str): Unique listing ID.
- `title` (str): Listing title.
- `description` (str): Longer item description.
- `category` (str): Clothing category, such as tops, bottoms, outerwear, shoes, or accessories.
- `style_tags` (list[str]): Style labels such as vintage, grunge, streetwear, minimal, etc.
- `size` (str): Listed item size.
- `condition` (str): Item condition, usually excellent, good, or fair.
- `price` (float): Item price.
- `colors` (list[str]): Main item colors.
- `brand` (str or null): Brand name if available.
- `platform` (str): Marketplace platform, stored as depop, thredUp, or poshmark.

The returned list should be sorted by relevance as best as possible, with the most useful match first. If no items match, it returns an empty list `[]` rather than crashing.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
If `search_listings` returns an empty list, the agent stores a helpful error message in session state and stops the workflow early. It should not call `suggest_outfit` or `create_fit_card` without a selected listing. The user should see a message like: “I couldn’t find a vintage graphic tee under $30 in that size. Try raising your budget, removing the size filter, or using a broader description like ‘graphic tee.’”

---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
`suggest_outfit` takes the selected thrift listing and the user's wardrobe, then recommends one or more ways to style the new item with pieces the user already owns. It should use the item's category, colors, style tags, and description, plus the wardrobe pieces, to generate a practical outfit suggestion.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): The selected listing dictionary returned from `search_listings`. It should include fields like `title`, `category`, `style_tags`, `colors`, `price`, `condition`, and `platform`.
- `wardrobe` (dict): The user's wardrobe data. It contains an `items` list, where each wardrobe item has fields: `id`, `name`, `category`, `colors`, `style_tags`, and `notes`.

**What it returns:**
<!-- Describe the return value -->
A string or structured outfit recommendation describing how to wear the new item. The recommendation should include:
- The selected new item.
- Existing wardrobe pieces to pair it with.
- Optional add-ons or layering pieces if available.
- Styling notes explaining why the pieces work together.

For example, it might recommend pairing a vintage graphic tee with baggy jeans and chunky sneakers, then explain how the silhouette and color contrast fit the user's style.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
If the wardrobe is empty or minimal, the tool should still return a useful suggestion using general styling advice instead of crashing. For example, it can say: “Your wardrobe is empty, so I’ll style this generally: pair the tee with relaxed denim, chunky sneakers, and a simple jacket.” If the LLM call fails, the tool should return a readable fallback suggestion instead of raising an exception.

---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
`create_fit_card` turns the completed outfit suggestion into a short, shareable fit card or caption. The result should sound more like a social post or styling caption than a plain product description.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): The outfit recommendation string returned by `suggest_outfit`, including the styling idea and wardrobe pieces.
- `new_item` (dict): The selected listing dictionary from `search_listings`, used to mention the thrifted item, price, platform, condition, and style details.

**What it returns:**
<!-- Describe the return value -->
A short string containing a shareable outfit description or caption. It should include the new thrifted item and the overall vibe of the outfit. It should produce different outputs for different inputs, and repeated calls should have some variation because it uses the LLM with a nonzero temperature.

Example output:
“thrifted this faded graphic tee for $24 and paired it with baggy denim + chunky sneakers for that effortless 2000s streetwear feel 🖤”

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
If the `outfit` input is missing, empty, or incomplete, the tool should return a clear error string like: “I need an outfit suggestion before I can create a fit card.” It should not crash or generate a caption from missing data. If the LLM call fails, it should return a simple fallback caption based on the new item and outfit details.

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->
No additional tools are planned for the required implementation. If I attempt a stretch feature later, I will update this section before implementing it.

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->
The agent starts with the user's natural language query and uses simple rule-based parsing (regex/string matching) to extract three search inputs stored in `session["parsed"]`: `description`, `size`, and `max_price`. For example, max price comes from phrases like "under $30", size from phrases like "size M", and the remaining item phrase becomes the description. If the user does not provide a size, `size` is set to `None`. If the user does not provide a budget, `max_price` is set to `None`.

The planning loop follows this conditional flow:

1. Initialize a session dictionary to track the interaction. The session starts with:
   - `query`: original user query
   - `parsed`: `{}` (will hold `description`, `size`, and `max_price`)
   - `search_results`: `[]`
   - `selected_item`: `None`
   - `wardrobe`: the wardrobe dict passed into `run_agent()`
   - `outfit_suggestion`: `None`
   - `fit_card`: `None`
   - `error`: `None`

2. Parse the query and store `description`, `size`, and `max_price` inside `session["parsed"]` (not as top-level session keys).

3. Call `search_listings(session["parsed"]["description"], session["parsed"]["size"], session["parsed"]["max_price"])`.

4. Check the search results:
   - If `search_results == []`, store an error message in `session["error"]` and return the session immediately. This is the only required early stop in the planning loop.
   - The agent does not call `suggest_outfit` or `create_fit_card` if no listing was found.
   - If results exist, store them in `session["search_results"]`.

5. Select the best item:
   - Set `session["selected_item"] = search_results[0]`.
   - The first result is treated as the top match because `search_listings` should return results in relevance order.

6. Call `suggest_outfit(session["selected_item"], session["wardrobe"])`.
   - Store the returned string in `session["outfit_suggestion"]`, even if it is fallback styling advice (for example, when the wardrobe is empty). The tool handles graceful fallbacks internally; the agent does not stop early here.

7. Call `create_fit_card(session["outfit_suggestion"], session["selected_item"])`.
   - Store the returned string in `session["fit_card"]`, whether it is a caption or a clear error/fallback message from the tool. The agent does not stop early here unless search already failed.

8. Return the complete session. The UI will display the selected listing, outfit suggestion, fit card, and any error message.

The agent is done when it either returns early after failed search results or successfully runs all three tools and stores a selected item, outfit suggestion, and fit card in session state.

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->
The agent manages state using a session dictionary that exists for one complete user interaction. Each tool's output is saved into this dictionary so the next tool can use it without asking the user to re-enter information.

The session stores:
- `query`: The original user request.
- `parsed`: A dict with `description`, `size`, and `max_price` extracted from the query.
- `wardrobe`: The wardrobe dictionary used for styling.
- `search_results`: The list returned by `search_listings` (starts as `[]`).
- `selected_item`: The first/best listing selected from the search results.
- `outfit_suggestion`: The result from `suggest_outfit`.
- `fit_card`: The result from `create_fit_card`.
- `error`: Any error or graceful failure message.

State flow:
- The user query is parsed into `session["parsed"]["description"]`, `session["parsed"]["size"]`, and `session["parsed"]["max_price"]`.
- `search_listings` returns `search_results`.
- `search_results[0]` becomes `selected_item`.
- `selected_item` and `wardrobe` are passed into `suggest_outfit`.
- `outfit_suggestion` and `selected_item` are passed into `create_fit_card`.
- The final session is returned to the UI so the user can see what happened.

This prevents the agent from losing important information between steps. For example, the exact listing selected during search is the same dictionary used later in the outfit suggestion and fit card.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | Store `session["error"] = "I couldn't find any listings that matched your search. Try broadening the description, removing the size filter, or increasing the max price."` Return the session early and do not call `suggest_outfit` or `create_fit_card`. |
| suggest_outfit | Wardrobe is empty | Return a useful general styling suggestion instead of crashing. The agent should tell the user it does not have much wardrobe data and suggest common pieces that would work with the new item. |
| create_fit_card | Outfit input is missing or incomplete | Return a clear error string such as `"I need an outfit suggestion before I can create a fit card."` The agent stores this in `session["error"]` and does not pretend a complete fit card was created. |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->
```mermaid
flowchart TD
    A[User query] --> B[Planning Loop]

    B --> C[Parse query into description, size, max_price]
    C --> D[Store in session parsed, query, wardrobe]

    D --> E[search_listings description, size, max_price]
    E --> F{Any search results?}

    F -- No --> G[Set session error: no listings found]
    G --> H[Return session early]
    H --> Z[User sees helpful retry suggestion]

    F -- Yes --> I[Store session search_results]
    I --> J[Select search_results[0]]
    J --> K[Store session selected_item]

    K --> L[suggest_outfit selected_item, wardrobe]
    L --> M[Store session outfit_suggestion]
    M --> N[Tool returns styling text or fallback if wardrobe empty]

    N --> O[create_fit_card outfit_suggestion, selected_item]
    O --> P[Store session fit_card]
    P --> Q[Tool returns caption or error/fallback string]

    Q --> R[Return complete session]
    R --> S[User sees selected item, outfit suggestion, and fit card]
```

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**

I will use Cursor as my AI coding assistant. For each required tool, I will give Cursor only the relevant tool block from this `planning.md`, plus the matching function stub from `tools.py`.

For `search_listings`, I will give Cursor the Tool 1 spec and ask it to implement `search_listings(description, size, max_price)` using `load_listings()` from `utils/data_loader.py`. I expect it to produce a function that filters by description keywords/style tags, optional size, and optional max price, then returns a list of listing dictionaries. Before trusting the code, I will verify that it uses `load_listings()` instead of rewriting file loading, handles `size=None`, handles `max_price=None`, returns `[]` when there are no matches, and never crashes on no results. I will test it with at least three queries: a normal match, an impossible match, and a strict price filter.

For `suggest_outfit`, I will give Cursor the Tool 2 spec and the existing stub from `tools.py`. I expect it to produce a Groq LLM call using `llama-3.3-70b-versatile` and `GROQ_API_KEY` from `.env`. Before trusting it, I will verify that it accepts `new_item` and `wardrobe`, handles `wardrobe["items"]` being empty, and returns a readable string rather than raising an exception.

For `create_fit_card`, I will give Cursor the Tool 3 spec and the actual function signature from `tools.py`. I expect it to produce a Groq LLM call that generates a short shareable caption using both `outfit` and `new_item`. Before trusting it, I will verify that it guards against empty outfit input, uses a nonzero temperature for variation, and returns a fallback string if the LLM call fails.

I will then write pytest tests in `tests/test_tools.py` to test each required failure mode before moving to the agent loop.

**Milestone 4 — Planning loop and state management:**

I will use Cursor to implement the planning loop in `agent.py`. I will give Cursor the `Planning Loop`, `State Management`, `Error Handling`, and `Architecture` sections from this `planning.md`, plus the existing TODOs in `agent.py`.

I expect Cursor to produce a `run_agent()` implementation that:
- Parses or receives the needed search inputs.
- Initializes and updates a session dictionary.
- Calls `search_listings` first.
- Checks whether search results are empty before continuing.
- Stores `selected_item = search_results[0]`.
- Passes the same `selected_item` into `suggest_outfit`.
- Passes `outfit_suggestion` and `selected_item` into `create_fit_card`.
- Returns the final session.

Before trusting the code, I will check that it does not call all three tools unconditionally. I will specifically test the no-results path and confirm that `session["error"]` is set while `session["selected_item"]`, `session["outfit_suggestion"]`, and `session["fit_card"]` stay `None`.

For `app.py`, I will give Cursor the `State Management` section and the TODO inside `handle_query()`. I expect it to map the returned session dictionary into the Gradio output panels. I will verify this by running `python app.py` and testing both a normal query and a no-results query in the browser.

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

FitFindr takes a natural language request about a secondhand clothing item and turns it into a multi-step styling workflow. First, it searches the mock listings data using the requested description, size, and max price; if no listings match, the agent stops and gives the user a helpful message instead of continuing with empty data. If a listing is found, the selected item is passed into the outfit suggestion tool along with the user's wardrobe, and that outfit suggestion is then passed into the fit card tool to generate a short shareable caption.

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
The agent parses the user's request and calls `search_listings` with:
- `description`: `"vintage graphic tee"`
- `size`: `None` because the user did not specify a size
- `max_price`: `30.0`

The tool filters `listings.json` for items matching the description, title, category, style tags, and price cap. It returns a list of matching listings, e.g.:
- `lst_006` — "Graphic Tee — 2003 Tour Bootleg Style", $24.00, size L, tags: graphic tee, vintage, grunge, streetwear
- `lst_033` — "Vintage Band Tee — Faded Grey", $19.00, size L, tags: vintage, grunge, band tee, graphic tee

The agent selects `lst_006` as the best match and stores the full listing dict in session state as `selected_item`.

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
Using the chosen listing from Step 1 and the user's wardrobe, the agent calls `suggest_outfit` with:
- `new_item`: the full `lst_006` listing dict
- `wardrobe`: the example wardrobe from `get_example_wardrobe()`

The tool pairs the new tee with existing wardrobe pieces that match the user's style, such as `w_001` "Baggy straight-leg jeans, dark wash" and `w_007` "Chunky white sneakers". It returns an outfit suggestion, e.g.:
- **New item:** Graphic Tee — 2003 Tour Bootleg Style ($24, Depop)
- **From wardrobe:** `w_001` Baggy straight-leg jeans, dark wash + `w_007` Chunky white sneakers
- **Optional add-on:** `w_006` Vintage black denim jacket
- **Styling notes:** The faded graphic tee works with relaxed denim and chunky sneakers for a vintage streetwear look.

The agent saves this outfit suggestion in session state as `outfit_suggestion`.

**Step 3:**
<!-- Continue until the full interaction is complete -->
The agent calls `create_fit_card` with:
- `outfit`: the outfit suggestion returned from Step 2
- `new_item`: the selected listing dict from Step 1

The tool turns the outfit recommendation and thrifted item details into a short, shareable fit card/caption. The agent saves this result in session state as `fit_card` and considers the interaction complete.

**Final output to user:**
<!-- What does the user actually see at the end? -->
The user sees the selected listing, the styling suggestion, and the fit card, for example:

> **Your FitFindr Pick**
>
> **New find:** Graphic Tee — 2003 Tour Bootleg Style — $24 on Depop, size L
>
> **Styled with your closet:**
> - `w_001` Baggy straight-leg jeans, dark wash
> - `w_007` Chunky white sneakers
> - Optional: `w_006` Vintage black denim jacket
>
> **Why it works:** The faded bootleg-style tee plays well with relaxed denim, and the chunky sneakers keep the look grounded in streetwear.
>
> **Fit card:** thrifted this faded graphic tee for $24 and paired it with baggy denim + chunky sneakers for that effortless vintage streetwear feel 🖤

If Step 1 returned no listings, the user would instead see a helpful message suggesting they broaden the description, remove the size filter, or increase the max price. The agent would stop there and would not call the outfit or fit card tools.