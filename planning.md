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

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): ...
- `size` (str): ...
- `max_price` (float): ...

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->

---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): ...
- `wardrobe` (dict): ...

**What it returns:**
<!-- Describe the return value -->

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->

---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (...): ...

**What it returns:**
<!-- Describe the return value -->

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | |
| suggest_outfit | Wardrobe is empty | |
| create_fit_card | Outfit input is missing or incomplete | |

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

**Milestone 4 — Planning loop and state management:**

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

FitFindr takes a natural language request about a secondhand clothing item and turns it into a multi-step styling workflow. First, it searches the mock listings data using the requested description, size, and max price; if no listings match, the agent stops and gives the user a helpful message instead of continuing with empty data. If a listing is found, the selected item is passed into the outfit suggestion tool along with the user's wardrobe, and that outfit suggestion is then passed into the fit card tool to generate a short shareable caption.

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
The agent parses the user's request and calls `search_listings` with:
- `description`: `"vintage graphic tee"`
- `size`: `"L"` (inferred from typical sizing, or omitted if the user did not specify)
- `max_price`: `30.0`

The tool filters `listings.json` for tops matching the description/style tags and price cap. It returns a list of matching listings, e.g.:
- `lst_006` — "Graphic Tee — 2003 Tour Bootleg Style", $24.00, size L, tags: graphic tee, vintage, grunge, streetwear
- `lst_033` — "Vintage Band Tee — Faded Grey", $19.00, size L, tags: vintage, grunge, band tee, graphic tee

The agent selects `lst_006` as the best match (vintage graphic tee, under budget, good condition) and stores it in session state as the chosen listing.

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
Using the chosen listing from Step 1 and the user's wardrobe (`get_example_wardrobe()`), the agent calls `suggest_outfit` with:
- `new_item`: the full `lst_006` listing dict
- `wardrobe`: the example wardrobe (baggy jeans `w_001`, chunky sneakers `w_007`, etc.)

The tool pairs the new tee with existing wardrobe pieces that match the user's style (baggy denim + chunky sneakers). It returns an outfit object, e.g.:
- **New item:** Graphic Tee — 2003 Tour Bootleg Style ($24, Depop)
- **From wardrobe:** Baggy straight-leg jeans, dark wash (`w_001`) + Chunky white sneakers (`w_007`)
- **Optional add-on:** Vintage black denim jacket (`w_006`) for layering
- **Styling notes:** Black tee + dark wash baggy jeans + white chunky sneakers — classic streetwear contrast; jacket adds structure without hiding the graphic.

The agent saves this outfit dict in session state for the next step.

**Step 3:**
<!-- Continue until the full interaction is complete -->
The agent calls `create_fit_card` with the outfit returned from Step 2. The tool formats the outfit into a structured fit card containing:
- The featured listing (title, price, platform, condition)
- Each wardrobe piece used (name, category)
- A short styling summary

The agent receives the fit card dict/string and considers the interaction complete — all three tools have run in sequence and state holds the listing, outfit, and fit card.

**Final output to user:**
<!-- What does the user actually see at the end? -->
The user sees a fit card summarizing the recommendation, for example:

> **Your FitFindr Pick**
>
> **New find:** Graphic Tee — 2003 Tour Bootleg Style — $24 on Depop (good condition, size L)
>
> **Styled with your closet:**
> - Baggy straight-leg jeans, dark wash
> - Chunky white sneakers
> - (Optional) Vintage black denim jacket
>
> **Why it works:** The faded black bootleg tee plays off your baggy dark-wash jeans, and the chunky white sneakers keep the look grounded in streetwear. Layer the denim jacket if you want extra edge without covering the graphic.
>
> **Also worth a look:** Vintage Band Tee — Faded Grey ($19 on Depop) if you prefer a softer grey palette.

The agent may briefly mention the alternate listing from Step 1 before closing the response.
