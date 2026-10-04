# Campus Customs Design

The key design decisions behind the Campus Customs site and its chat assistant, and why each was made. For full technical detail see `harness.md`. For the usability work and its measurements see `usability.md`.

## Goals

1. **Shoppers find the right item, in their size, quickly**, by browsing or by asking.
2. **Every answer about price and stock is correct**: it comes from the database, never from the model's guess.
3. **It feels like a real Yale shop**: refined, academic and trustworthy.

## Visual design

| Element | Choice | Why |
|---|---|---|
| Color | Yale blue `#00356b` as the main color, with Yale's secondary blues (`#286dc0`, `#63aaff`), white, and neutral grays. Red and green appear only for "out of stock" and "in stock". | One restrained palette looks official, and stock status stands out because nothing else uses those colors. |
| Type | EB Garamond (headings) and Libre Franklin (body). Both are open-licence and self-hosted. | An old-style serif in the spirit of Yale's typeface gives the academic feel; a clean sans keeps prices, sizes and chat easy to read on phones. |
| Crest and motto | An original shield with an open book in the style of Yale's arms, plus "Lux et Veritas", in the header, footer, tab icon, home banner and About page. | Signals "Yale store" at a glance without copying Yale's trademarked artwork. |
| Mascot | Handsome Dan, an original cartoon bulldog in a Yale-blue collar, is the face of the chat. | Turns "a chatbot" into a friendly guide shoppers want to ask. |
| Whitespace | Generous margins, 4-column product grid on desktop, 1 column on phones. | Product photos carry the page; text stays scannable. |

## Page structure

- **Header:** a slim top bar ("Lux et Veritas" and "Ask Handsome Dan about sizes and stock"), then the crest logo, Home / Products / About Us, and Log In / Create Account (or "Hi, [name]" and Log Out).
- **Home:** a hero banner, "Shop by residential college" buttons, and four featured rows (layers, game day, family, colleges). The rows are built from hand-picked catalogue IDs, so every item shown is real stock.
- **Products:**
  - A filter bar: keywords, category, color, size in stock and sort.
  - A grid of product cards: image, name, price, two-line description and "Ask about this".
  - Filters live in the URL, so they survive refresh and can be shared.
- **Product page:** large image on the left. On the right: category, name, price, full description, design colors, a box per size with its stock (or "Out of stock") and "Ask about this".
- **About, Log In, Create Account:** simple, centered pages in the same style. The About page states only facts drawn from the catalogue.

## Chat experience

| Decision | Why |
|---|---|
| The chat starts as a button in the bottom-right corner and opens into a panel there. | Always reachable, never in the way. |
| The panel never covers the page: on desktop the page makes room beside it; on phones the page scrolls above it. | Shoppers can read a product page while asking about it. |
| History follows the shopper from page to page. Logged-in shoppers' chats are saved to their account; guests' last only for the tab. | Conversations aren't lost when browsing; privacy for guests and shared computers. |
| "Ask about this" on every card and product page, and the page itself as context. | "Do you have this in pink?" just works. |
| Suggested questions that change with the page. | Easy first step, especially on phones. |
| Replies show product cards; browsing questions switch the main page to every match. | Answers lead straight to the products. |
| Handsome Dan speaks in a calm, warm narrator's voice, briefly, in plain text. | Friendly but efficient; facts first. |

## Technical design choices

| Decision | Why |
|---|---|
| The agent answers only from typed tool results (`models.py`) computed from the database. | Prices and stock are always correct, and field names like `design_colors` and `stock_status` steer the model. |
| The agent's output holds references (product IDs, search filters), not product data. FastAPI rebuilds cards and re-runs searches. | A model mistake can't show a fake product or price. |
| The agent's search and the page's filters share one search function. | The page always shows exactly what the chat described, with the same color and hoodie rules. |
| Identity comes from a server-side session cookie, never from the chat. | Nobody can talk their way into someone else's account or history. |
| Compact list results and a one-step `find_product` tool. | About 11% fewer tokens and 19% faster answers on the benchmark (`usability.md`). |
| Layered safety: prompt rules, code checks (crisis safety net, content-filter fallback, input and loop limits) and an append-only audit trail. | Rules guide the model; code catches what rules can't guarantee; the audit trail lets every answer be reviewed. |

## Store rules reflected in the design

- Navy and navy blue are one color; royal blue and light blue are separate; "blue" covers all of them.
- Every hooded style counts as a hoodie.
- A product's colors describe its one design, not options to choose from.
- There's no cart or checkout, and nothing on the site or in the chat suggests there is.
