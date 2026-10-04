# Usability Improvements

Problem 9 adds two improvements to the shopping experience on the website (suggested questions in the chat, and filters and sorting on the Products page) and two to the backend that make the chat assistant faster and cheaper to run (lean search results, and a one-step `find_product` tool). Each section says what was added, why it helps, and how it was checked.

The chat already had a reset button: "Clear", added in Problem 8. So the two frontend improvements below are new features.

---

## Frontend improvement 1: Suggested questions in the chat

**What changed.** The chat shows tappable suggested questions just above the text box. Tapping one sends it. The suggestions change with the page (`frontend/src/chat/suggestions.ts` and `ChatWidget.tsx`):

| Where the shopper is | Suggestions |
|---|---|
| Home, About or any other page (shown while the chat is empty) | What kinds of t-shirts do you have? · Show me navy hoodies under $70 · Anything with a bulldog on it? · What crewnecks do you have in XL? |
| A product page, or after "Ask about this" | What sizes are in stock? · Does this come in other colors? · Show me similar items |
| Search results | Which of these are in stock in M? · Which of these is the cheapest? · Show me these in gray |

On product and search pages, the suggestions stay visible after the first message. Elsewhere they disappear once the conversation starts, so they don't get in the way.

**Why it helps the customer.**
- An empty chat box is hard to start. Many shoppers don't know what a store's assistant can do, or what to type.
- One tap gets an answer, which matters most on a phone, where typing is slow.
- The page-specific suggestions show off what the assistant does best: stock by size, colors, similar items, and narrowing search results. Shoppers learn those features exist.

**Why it helps the website.** Starter questions are already phrased in a way the assistant handles well, so the first answers are reliable. The browsing suggestions also lead into the page-updating search from Problem 7.

**Checked.**
- In the browser, each page showed the right set of suggestions.
- Tapping "What sizes are in stock?" on the Basic Hoodie Big Yale page answered "in stock in every size: XS, S, M, L, XL and XXL" (correct).
- Tapping "Show me navy hoodies under $70" on the home page updated the page to the 23 matching hoodies, and the suggestions switched to the search-results set.

## Frontend improvement 2: Filters and sorting on the Products page

**What changed.** The Products page has a filter bar (`frontend/src/pages/Products.tsx`):
- **Search box:** keywords such as "Saybrook", "bulldog" or "hockey".
- **Category:** hoodies, crewnecks, T-shirts, quarter-zips, jackets, long-sleeve shirts, mocknecks.
- **Color:** navy, "blue (all shades)", royal blue, light blue, gray, white and more.
- **In stock in:** XS to XXL.
- **Sort:** featured, price low to high, price high to low, name A to Z.

The heading shows how many styles match, with a "Clear filters" link. If nothing matches, the page says so and offers to clear the filters.

**How it works.**
- Filters are stored in the page address (for example `/products?category=hoodie&color=navy&size_in_stock=XL&sort=price-desc`), so refresh, back, forward and sharing a link all work.
- They use the same `GET /api/search` as the chat's page search. That means the store's rules apply the same way everywhere: navy equals navy blue, "blue" includes every blue, and every hooded style counts as a hoodie.
- **The chat and the filters stay in sync.** When the assistant updates the page ("navy hoodies under $70"), the filter bar shows Category = Hoodies and Color = Navy. The shopper can then adjust those filters by hand.

**Why it helps the customer.**
- Before, the only ways to narrow 102 products were scrolling or asking the chat. Many shoppers would rather click than type.
- "In stock in my size" is the filter that saves the most frustration: no more opening a product only to find the size is sold out.
- Sorting by price helps shoppers on a budget.

**Why it helps the website.** Shoppers who find what they want quickly are more likely to buy. It also takes simple filtering questions off the chat, and each chat question costs model tokens, while a filter costs nothing.

**Checked** (browser, desktop and phone):

| Step | Result |
|---|---|
| Category = Hoodies | 27 styles |
| + Color = Navy, In stock in = XL | 19 styles (matches a direct database count of 19) |
| Sort = Price: high to low | $88.00 items first |
| Clear filters | Back to all 102, sort kept |
| Search "saybrook" | 3 styles |
| + Category = Mocknecks | "No products match these filters. Clear filters" |

On a phone, the filter bar wraps neatly above the product grid.

---

## Starting point for the backend (measured before any changes)

Five typical shopper questions were run against the live agent (Luna through Portkey), recording model calls, tokens and time:

| Question | Model calls | Input tokens | Output tokens | Time |
|---|---|---|---|---|
| What kinds of t shirts do you have? | 2 | 10,854 | 278 | 3.2 s |
| Show me navy hoodies under $70 | 2 | 10,805 | 437 | 5.0 s |
| Do you have the Ice Hockey Left Chest Hoodie in a large? | 4 | 18,988 | 381 | 11.5 s |
| Is this in stock in medium? (on a product page) | 2 | 8,757 | 111 | 4.4 s |
| What crewnecks do you have in XL? | 2 | 10,879 | 333 | 4.5 s |
| **Total** | **12** | **60,283** | **1,540** | **28.6 s** |

What this showed:

- **Input tokens are almost all of the cost.** The model reads about 40 input tokens for every one it writes. Each model call re-reads the system prompt, the tool descriptions and every tool result so far.
- **Model calls are almost all of the wait.** The database tools take about 1 millisecond. The model takes seconds per call.
- So the backend improvements focus on fewer model calls and smaller tool results, not on database speed. A database cache was considered and dropped, because it would save about 1 ms on a 4-second answer.

---

## Backend improvement 1: Lean search results

**What changed.**
- `search_products` and `find_similar_products` now return a compact `ProductBrief` for each product instead of the full `ProductInfo` record (`models.py`, `tools.py`). A brief has name, category, price, design colors, stock status and the list of sizes in stock.
- The full description and per-size counts are still one call away, through `get_product_details` or `check_stock`.
- The search's default limit went from 8 to 6, the same as the most product cards a reply can show.

**Why it helps.**
- A search result stays in the conversation, and the model re-reads it on every later call. So a smaller result saves tokens more than once.
- A list answer ("here are six hoodies") never needed the full descriptions.

**Measured.** The tool result for "t-shirts" shrank from 5,870 characters (8 full records) to 1,557 characters (6 briefs), **73% smaller**. Each browsing question dropped from about 10,850 to about 9,480 input tokens before the prompt grew to describe the new `find_product` tool (below), and about 9,740 after.

## Backend improvement 2: One-step `find_product` tool

**What changed.**
- A new agent tool, `find_product(name, size)` (`tools.py`, returning `NamedProduct` in `models.py`), finds a product by the name the shopper typed and checks a size in the same call.
- It treats "1/4 Zip", "1-4 zip" and "1 4 Zip" as the same, ignores capitals and filler words, and lists other close matches.
- If several products match a vague name equally well (for example "yale t-shirt"), it doesn't pick one at random. It returns them as options so the assistant can ask which one the shopper means.
- The prompt tells the agent to use it whenever a shopper names a product.

**Why it helps.**
- "Is the Basic Hoodie Big Yale in stock in medium?" used to take three model calls: search for the name, check stock, then answer. It now takes two.
- Every model call skipped saves the shopper about 1.5 to 2 seconds and saves about 4,000 input tokens.
- Asking "which one?" instead of guessing also stops the assistant from answering about the wrong product.

**Measured** (same questions, Luna):

Before this tool, a named-product stock question always followed the same pattern: `search_products`, then `check_stock`, then the answer. That's 3 model calls, about 13,900 input tokens (measured on "Ice Hockey Left Chest Hoodie in a large?" with lean results already in place). With `find_product`:

| Named-product question | Model calls | Input tokens | Answer |
|---|---|---|---|
| Is the Basic Hoodie Big Yale in stock in medium? | **2** | 9,524 | "in stock in medium, with 5 available" (correct) |
| How much is the Davenport College Crewneck, and do you have it in XXL? | **2** | 9,752 | "$58.00… 8 available" (correct) |
| Do you have the Fencing Left Chest Hoodie in XS? | 3 (2 + a call for alternatives) | 15,183 | "out of stock in XS", plus three in-stock alternatives (correct) |
| Is the yale t-shirt in stock? | 2 | 9,556 | Asks which of the 3 Yale T-shirts the shopper means |

### Combined effect on the same five benchmark questions

| | Before | After | Change |
|---|---|---|---|
| Model calls | 12 | 11 | −1 |
| Input tokens | 60,283 | 53,829 | **−10.7%** |
| Output tokens | 1,540 | 1,395 | −9.4% |
| Total time | 28.6 s | 23.1 s | **−19%** |

The biggest single gain was the named-product question ("Ice Hockey Left Chest Hoodie in a large?"): **11.5 s → 6.9 s**, with 4 model calls down to 3 and 18,988 tokens down to 15,168. The remaining third call is the assistant fetching in-stock alternatives, because that size is sold out.

### Tried and dropped: preloading the product on screen

I also tried putting the current product's price and stock straight into the agent's instructions whenever the shopper was on a product page, hoping "Is this in M?" would need no tool call. Luna still called a lookup tool every time, even when told it didn't need to; it seems built to verify facts with a tool. The preload saved no model calls and added about 350 tokens to every message, so it was removed. Keeping it would have made things slower and more expensive.


---

## Does everything still work?

After all four changes, the whole site was re-checked:

- **Build:** the frontend type-checks, lints and builds with no errors or warnings.
- **12 chat checks against the live site** (as a guest, so nothing was saved): **12/12 passed**.
  - prompt-injection attempt refused politely
  - off-topic request declined
  - card number not repeated
  - "Are you Morgan Freeman?" answered honestly
  - "Do you have this in pink?" on a product page
  - out-of-stock size reported clearly
  - named product out of stock in L reported, not swapped for another item
  - T-shirt search updates the page with all 25
  - Handsome Dan leads to bulldog items
  - no made-up return policy
  - a guest isn't told who they are
  - a previously placeholder product described from its new data
- **Accounts:** login, "who am I", logout.
- **Pages:** product list (102), search (25 T-shirts) and product details all work.
- **Customer memory (on a copy of the database):** a logged-in question was saved. After logging in again, the history had grown from 6 to 8 messages, and the assistant remembered "You just asked about the Davenport College Crewneck."
- **Browser:**
  - Filters, sorting, keyword search and suggestions worked on desktop and phone.
  - The chat's page search filled in the filter bar.
  - The browser console showed no errors.
- **Real database untouched by testing:** still 3 users and 22 saved chat messages.
