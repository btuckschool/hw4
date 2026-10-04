"""Catalogue queries, shared by the API routes and the chat agent's tools.

Every price, size and stock number the agent quotes comes from these functions,
which read the live database. The agent never sees prices any other way.
"""

import json
import os
import re
import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path

from pydantic_ai import RunContext

from models import (
    CatalogueOverview,
    CategorySummary,
    ChatDeps,
    ChatTurn,
    CustomerProfile,
    ProductDetail,
    ProductBrief,
    ProductFilters,
    ProductInfo,
    NamedProduct,
    ProductLookup,
    ProductSummary,
    SavedMessage,
    SearchResults,
    SimilarProducts,
    SizeAvailability,
    SizeStock,
    StockCheck,
    StockStatus,
)

DATA_DIR = Path(os.environ.get("CAMPUS_CUSTOMS_DATA", Path(__file__).resolve().parent.parent / "data"))
DB_PATH = DATA_DIR / "campus_customs.db"
IMAGES_DIR = DATA_DIR / "products"

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]


@contextmanager
def db(write: bool = False):
    # Read-only by default; only account creation opens a writable connection.
    uri = f"file:{DB_PATH}" if write else f"file:{DB_PATH}?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        with conn:
            yield conn


def image_url(image_file_path: str) -> str:
    # Stored as "products/<file>.jpg"; served from /images/<file>.jpg.
    return f"/images/{Path(image_file_path).name}"


def size_rank(size: str) -> int:
    return SIZE_ORDER.index(size) if size in SIZE_ORDER else len(SIZE_ORDER)


# ---------- Matching rules (see "Decisions" in output/harness.md) ----------

CATEGORIES = ["hoodie", "crewneck", "t-shirt", "quarter-zip", "jacket", "long-sleeve shirt", "mockneck"]


def category_of(garment_type: str) -> str:
    """Group the catalogue's varied garment_type labels into shopper-facing categories."""
    g = garment_type.lower()
    if "hood" in g:  # hoodie, pullover hoodie, hooded sweatshirt, full-zip hooded sweatshirt...
        return "hoodie"
    if "quarter-zip" in g:
        return "quarter-zip"
    if "jacket" in g:  # fleece, full-zip fleece and bomber jackets
        return "jacket"
    if "t-shirt" in g:
        return "t-shirt"
    if "performance shirt" in g:
        return "long-sleeve shirt"
    if "mockneck" in g:
        return "mockneck"
    if "crewneck" in g:
        return "crewneck"
    return g


NAVY = {"navy", "navy blue"}
BLUE_FAMILY = NAVY | {"blue", "royal blue", "light blue"}


def color_matches(wanted: str, colors: list[str]) -> bool:
    """navy == navy blue; royal and light blue are their own colors; "blue" means any blue."""
    w = wanted.strip().lower().replace("grey", "gray")
    have = [c.lower() for c in colors]
    if w in NAVY:
        return any(c in NAVY for c in have)
    if w == "blue":
        return any(c in BLUE_FAMILY for c in have)
    if w in BLUE_FAMILY:
        return w in have
    return any(w in c for c in have)


# Hyphenated words stay whole, so "shorts" doesn't match "short-sleeve".
_TOKEN = re.compile(r"[a-z0-9&/'-]+")
_FILLER = {
    "a", "an", "and", "any", "anything", "are", "do", "for", "have", "i", "in", "is", "it",
    "me", "of", "on", "or", "some", "something", "the", "to", "with", "you", "your",
}


def _tokens(text: str) -> set[str]:
    return set(_TOKEN.findall(text.lower()))


# Words that are their own thing, not the plural of another word ("shorts" isn't "short").
_ALWAYS_PLURAL = {"shorts", "pants", "sweatpants", "joggers", "leggings", "socks", "glasses"}


def _word_matches(word: str, tokens: set[str]) -> bool:
    """Whole-word match that also accepts simple plurals (hoodie/hoodies, crest/crests)."""
    if word in _ALWAYS_PLURAL:
        return word in tokens
    return any(t == word or t + "s" == word or t + "es" == word or word + "s" == t for t in tokens)


# ---------- Queries ----------


def _load_products() -> list[dict]:
    with db() as conn:
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
        stock = conn.execute("SELECT product_id, size, quantity FROM inventory").fetchall()
    sizes: dict[str, list[SizeStock]] = {}
    for s in stock:
        sizes.setdefault(s["product_id"], []).append(SizeStock(size=s["size"], quantity=s["quantity"]))
    products = []
    for r in rows:
        product_sizes = sorted(sizes.get(r["product_id"], []), key=lambda s: size_rank(s.size))
        products.append(
            {
                "row": r,
                "colors": json.loads(r["colors"]),
                "tags": json.loads(r["search_tags"]),
                "sizes": product_sizes,
                "total": sum(s.quantity for s in product_sizes),
                "category": category_of(r["garment_type"]),
            }
        )
    return products


def _summary(p: dict) -> ProductSummary:
    r = p["row"]
    return ProductSummary(
        product_id=r["product_id"],
        name=r["name"],
        garment_type=r["garment_type"],
        description=r["description"],
        colors=p["colors"],
        price=r["price"],
        image_url=image_url(r["image_file_path"]),
        in_stock=p["total"] > 0,
    )


def _detail(p: dict) -> ProductDetail:
    return ProductDetail(
        **_summary(p).model_dump(),
        search_tags=p["tags"],
        sizes=p["sizes"],
        total_stock=p["total"],
    )


def all_products() -> list[ProductSummary]:
    return [_summary(p) for p in _load_products()]


def product_detail(product_id: str) -> ProductDetail | None:
    for p in _load_products():
        if p["row"]["product_id"] == product_id:
            return _detail(p)
    return None


def product_cards(product_ids: list[str]) -> list[ProductSummary]:
    """Summaries for the given IDs, in order, silently skipping any that don't exist."""
    by_id = {p["row"]["product_id"]: p for p in _load_products()}
    seen: set[str] = set()
    cards = []
    for pid in product_ids:
        if pid in by_id and pid not in seen:
            seen.add(pid)
            cards.append(_summary(by_id[pid]))
    return cards


def has_real_description(description: str) -> bool:
    # A few catalogue rows hold an auto-generated placeholder instead of a description.
    return "filename-based stub" not in description


def _stock_status(p: dict) -> StockStatus:
    if p["total"] == 0:
        return "sold_out"
    if any(s.quantity == 0 for s in p["sizes"]):
        return "some_sizes_sold_out"
    return "in_stock"


def _info(p: dict) -> ProductInfo:
    """Product facts for the model, straight from the database row and its inventory."""
    r = p["row"]
    return ProductInfo(
        product_id=r["product_id"],
        name=r["name"],
        category=p["category"],
        garment_type=r["garment_type"],
        price=r["price"],
        description=r["description"] if has_real_description(r["description"]) else None,
        design_colors=p["colors"],
        stock_status=_stock_status(p),
        total_stock=p["total"],
        sizes=[SizeAvailability(size=s.size, quantity=s.quantity, in_stock=s.quantity > 0) for s in p["sizes"]],
    )


def _brief(p: dict) -> ProductBrief:
    """Compact list entry: enough to compare and recommend, a fraction of the tokens."""
    r = p["row"]
    return ProductBrief(
        product_id=r["product_id"],
        name=r["name"],
        category=p["category"],
        price=r["price"],
        design_colors=p["colors"],
        stock_status=_stock_status(p),
        sizes_in_stock=[s.size for s in p["sizes"] if s.quantity > 0],
    )


def _find(products: list[dict], product_id: str) -> dict | None:
    pid = product_id.strip()
    return next((p for p in products if p["row"]["product_id"] == pid), None)


def _not_found(product_id: str) -> str:
    return f"No product with ID {product_id!r}. Use search_products to find the right ID."


def _match(products: list[dict], f: ProductFilters) -> tuple[list[dict], list[dict], bool]:
    """Apply search filters. Returns (matches, items only excluded by the size filter, keywords used).

    Both the agent's search tool and the Products page's search use this, so a search the
    agent describes in chat shows exactly the same items on the page.
    """
    scored = []
    sold_out_in_size = []
    words = [w for w in _TOKEN.findall((f.keywords or "").lower()) if w not in _FILLER]
    for p in products:
        r = p["row"]
        if f.category and p["category"] != f.category.strip().lower():
            continue
        if f.color and not color_matches(f.color, p["colors"]):
            continue
        if f.min_price is not None and r["price"] < f.min_price:
            continue
        if f.max_price is not None and r["price"] > f.max_price:
            continue
        score = 0
        if words:
            # Every keyword must appear; words in the name or tags rank higher than the description.
            strong = _tokens(" ".join([r["name"], r["garment_type"], " ".join(p["tags"])]))
            weak = _tokens(" ".join([r["description"], " ".join(p["colors"])]))
            if not all(_word_matches(w, strong | weak) for w in words):
                continue
            score = sum(2 if _word_matches(w, strong) else 1 for w in words)
        # The size filter goes last so items it removes can be reported, not silently dropped.
        if f.size_in_stock and not any(
            s.size == f.size_in_stock.strip().upper() and s.quantity > 0 for s in p["sizes"]
        ):
            sold_out_in_size.append((score, p))
            continue
        scored.append((score, p))

    scored.sort(key=lambda sp: (-sp[0], sp[1]["row"]["price"], sp[1]["row"]["name"]))
    sold_out_in_size.sort(key=lambda sp: -sp[0])
    return [p for _, p in scored], [p for _, p in sold_out_in_size], bool(words)


def search_catalogue(filters: ProductFilters) -> list[ProductSummary]:
    """Every product matching the filters, as product cards, in search order."""
    matches, _, _ = _match(_load_products(), filters)
    return [_summary(p) for p in matches]


# ---------- Agent tools ----------


def search_products(
    ctx: RunContext[ChatDeps],
    keywords: str | None = None,
    category: str | None = None,
    color: str | None = None,
    size_in_stock: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    limit: int = 6,
) -> SearchResults:
    """Search the Campus Customs catalogue. Every argument is optional; combine them to narrow results.

    Returns brief entries (name, price, colors, stock status, sizes in stock). For a product's
    description or exact quantities, use get_product_details or check_stock.

    Args:
        keywords: Words that must all appear in a product's name, description or tags, e.g.
            "bulldog", "Saybrook", "football", "law school". Use few, specific words; put
            garment type, color, size and price in the other filters instead.
        category: One of: hoodie, crewneck, t-shirt, quarter-zip, jacket, long-sleeve shirt, mockneck.
        color: A design color, e.g. "navy", "blue", "royal blue", "light blue", "gray", "white".
        size_in_stock: Only return products with stock in this size: XS, S, M, L, XL or XXL.
            Use it for browsing, not for checking a specific product (use check_stock for that).
        min_price: Lowest price in US dollars.
        max_price: Highest price in US dollars.
        limit: Maximum number of products to return (1 to 12). The default of 6 matches the
            number of product cards a reply can show.
    """
    filters = ProductFilters(
        keywords=keywords,
        category=category,
        color=color,
        size_in_stock=size_in_stock,
        min_price=min_price,
        max_price=max_price,
    )
    matches, sold_out_in_size, used_keywords = _match(_load_products(), filters)
    limit = max(1, min(limit, 12))
    results = [_brief(p) for p in matches[:limit]]
    # Only worth reporting for targeted searches, where the shopper likely meant these items.
    report_sold_out = used_keywords and len(sold_out_in_size) <= 5
    return SearchResults(
        total_matches=len(matches),
        returned=len(results),
        filters_used=filters.model_dump(exclude_none=True),
        products=results,
        out_of_stock_in_requested_size=[_brief(p) for p in sold_out_in_size] if report_sold_out else [],
    )


def get_product_details(ctx: RunContext[ChatDeps], product_id: str) -> ProductLookup:
    """Look up one product: full description, price, design colors and current stock in every size.

    Args:
        product_id: The product's ID, e.g. "basic-hoodie-big-yale".
    """
    p = _find(_load_products(), product_id)
    if p is None:
        return ProductLookup(found=False, message=_not_found(product_id))
    return ProductLookup(found=True, product=_info(p))


def check_stock(ctx: RunContext[ChatDeps], product_id: str, size: str | None = None) -> StockCheck:
    """Check whether a product is in stock, overall or in one size. Use this for any availability question.

    Args:
        product_id: The product's ID, e.g. "basic-hoodie-big-yale".
        size: Optional size to check: XS, S, M, L, XL or XXL.
    """
    p = _find(_load_products(), product_id)
    if p is None:
        return StockCheck(found=False, product_id=product_id, message=_not_found(product_id))

    name, price = p["row"]["name"], p["row"]["price"]
    in_stock = [s.size for s in p["sizes"] if s.quantity > 0]
    out = [s.size for s in p["sizes"] if s.quantity == 0]
    result = StockCheck(
        found=True,
        product_id=p["row"]["product_id"],
        name=name,
        price=price,
        stock_status=_stock_status(p),
        sizes_in_stock=in_stock,
        sizes_out_of_stock=out,
        message="",
    )
    available = ", ".join(in_stock) or "none"

    if size:
        wanted = size.strip().upper()
        match = next((s for s in p["sizes"] if s.size == wanted), None)
        result.requested_size = wanted
        if match is None:
            result.message = f"{name} isn't offered in size {wanted}. Sizes in stock: {available}."
        elif match.quantity > 0:
            result.requested_size_quantity = match.quantity
            result.requested_size_in_stock = True
            result.message = f"{name} is in stock in {wanted} ({match.quantity} available)."
        else:
            result.requested_size_quantity = 0
            result.requested_size_in_stock = False
            result.message = f"{name} is out of stock in {wanted}. Sizes in stock: {available}."
    elif not in_stock:
        result.message = f"{name} is out of stock in every size."
    elif out:
        result.message = f"{name} is in stock in {available}; out of stock in {', '.join(out)}."
    else:
        result.message = f"{name} is in stock in every size ({available})."
    return result


def _name_tokens(text: str) -> set[str]:
    # "1/4 Zip", "1-4 zip" and "1 4 Zip" all compare equal; so do "T-Shirt" and "T Shirt".
    cleaned = re.sub(r"[^a-z0-9]+", " ", text.lower().replace("'", ""))
    return {t for t in cleaned.split() if t not in _FILLER}


def find_product(ctx: RunContext[ChatDeps], name: str, size: str | None = None) -> NamedProduct:
    """Look up a product the shopper named, and optionally its stock in one size, in a single step.

    Use this whenever the shopper names a specific product ("the Ice Hockey Left Chest Hoodie
    in large"), instead of search_products followed by check_stock.

    Args:
        name: The product name as the shopper wrote it, e.g. "Basic Hoodie Big Yale".
        size: Optional size to check: XS, S, M, L, XL or XXL.
    """
    wanted = _name_tokens(name)
    products = _load_products()
    scored = []
    for p in products:
        have = _name_tokens(p["row"]["name"])
        if not wanted or not have:
            continue
        overlap = len(wanted & have)
        # Share of the shopper's words found in the name, lightly penalizing extra name words.
        score = overlap / len(wanted) - 0.05 * len(have - wanted)
        if overlap:
            scored.append((score, p))
    scored.sort(key=lambda sp: -sp[0])

    if not scored or scored[0][0] < 0.6:
        return NamedProduct(
            found=False,
            query=name,
            other_close_matches=[_brief(p) for _, p in scored[:3]],
            message=f"No product named {name!r}. Try search_products with keywords instead.",
        )

    # Several names fit equally well ("yale t-shirt"): don't pick one at random.
    if len(scored) > 1 and scored[1][0] >= scored[0][0] - 0.01:
        ties = [p for sc, p in scored if sc >= scored[0][0] - 0.01]
        return NamedProduct(
            found=False,
            query=name,
            other_close_matches=[_brief(p) for p in ties[:6]],
            message=(
                f"{len(ties)} products match {name!r} equally well. Ask which one the shopper means, "
                "or use search_products to browse them."
            ),
        )

    best = scored[0][1]
    info = _info(best)
    result = NamedProduct(
        found=True,
        query=name,
        product=info,
        other_close_matches=[_brief(p) for sc, p in scored[1:4] if sc >= 0.5],
        message="",
    )
    available = ", ".join(s.size for s in best["sizes"] if s.quantity > 0) or "none"
    if size:
        want = size.strip().upper()
        match = next((s for s in best["sizes"] if s.size == want), None)
        result.requested_size = want
        if match is None:
            result.message = f"{info.name} isn't offered in size {want}. Sizes in stock: {available}."
        else:
            result.requested_size_quantity = match.quantity
            result.requested_size_in_stock = match.quantity > 0
            result.message = (
                f"{info.name} is in stock in {want} ({match.quantity} available)."
                if match.quantity > 0
                else f"{info.name} is out of stock in {want}. Sizes in stock: {available}."
            )
    else:
        result.message = f"Found {info.name} (${info.price:.2f}). Sizes in stock: {available}."
    return result


def find_similar_products(ctx: RunContext[ChatDeps], product_id: str, limit: int = 4) -> SimilarProducts:
    """Find in-stock products similar to a given one: same category first, then shared design colors and tags.

    Args:
        product_id: The product to compare against.
        limit: Maximum number of similar products to return (1 to 8).
    """
    products = _load_products()
    base = _find(products, product_id)
    if base is None:
        return SimilarProducts(found=False, similar_to=product_id, message=_not_found(product_id))
    base_colors = {c.lower() for c in base["colors"]}
    base_tags = {t.lower() for t in base["tags"]}

    def score(p: dict) -> float:
        s = 3.0 if p["category"] == base["category"] else 0.0
        s += len(base_colors & {c.lower() for c in p["colors"]})
        s += 0.5 * len(base_tags & {t.lower() for t in p["tags"]})
        s -= abs(p["row"]["price"] - base["row"]["price"]) / 100
        return s

    others = [p for p in products if p is not base and p["total"] > 0]
    others.sort(key=score, reverse=True)
    limit = max(1, min(limit, 8))
    return SimilarProducts(
        found=True, similar_to=base["row"]["product_id"], products=[_brief(p) for p in others[:limit]]
    )


def catalogue_overview(ctx: RunContext[ChatDeps]) -> CatalogueOverview:
    """Summarize what the store carries: product count, how many have stock, and price range per category."""
    products = _load_products()
    groups: dict[str, list[dict]] = {}
    for p in products:
        groups.setdefault(p["category"], []).append(p)
    return CatalogueOverview(
        total_products=len(products),
        sizes_offered=SIZE_ORDER,
        categories=[
            CategorySummary(
                category=c,
                product_count=len(ps),
                products_with_stock=sum(1 for p in ps if p["total"] > 0),
                min_price=min(p["row"]["price"] for p in ps),
                max_price=max(p["row"]["price"] for p in ps),
            )
            for c, ps in sorted(groups.items(), key=lambda kv: -len(kv[1]))
        ],
    )


def get_customer_profile(ctx: RunContext[ChatDeps]) -> CustomerProfile:
    """Who is chatting: name, email, member-since date and saved message count for a logged-in shopper.

    Returns logged_in=False and nothing else for guests.
    """
    if ctx.deps.user_id is None:
        return CustomerProfile(logged_in=False)
    with db() as conn:
        row = conn.execute("SELECT created_at FROM users WHERE id = ?", (ctx.deps.user_id,)).fetchone()
        count = conn.execute(
            "SELECT COUNT(*) FROM chat_messages WHERE user_id = ?", (ctx.deps.user_id,)
        ).fetchone()[0]
    return CustomerProfile(
        logged_in=True,
        first_name=ctx.deps.first_name,
        last_name=ctx.deps.last_name,
        email=ctx.deps.email,
        member_since=row["created_at"][:10] if row else None,
        saved_messages=count,
    )


AGENT_TOOLS = [
    search_products,
    find_product,
    get_product_details,
    check_stock,
    find_similar_products,
    catalogue_overview,
    get_customer_profile,
]


# ---------- Saved chat history (logged-in shoppers only) ----------

HISTORY_LIMIT = 50  # most recent messages shown when a shopper logs back in


def _product_ids(products_json: str | None) -> list[str]:
    # Saved as a list of product objects; older rows hold full snapshots, newer ones cards.
    # Only the IDs are used, so cards always show today's name, image and price.
    if not products_json:
        return []
    try:
        return [p["product_id"] for p in json.loads(products_json) if isinstance(p, dict) and "product_id" in p]
    except (ValueError, TypeError):
        return []


def load_history(user_id: int, limit: int = HISTORY_LIMIT) -> list[SavedMessage]:
    with db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM (
                SELECT id, role, content, products_json, created_at FROM chat_messages
                WHERE user_id = ? AND role IN ('user', 'assistant')
                ORDER BY id DESC LIMIT ?
            ) ORDER BY id
            """,
            (user_id, limit),
        ).fetchall()
    return [
        SavedMessage(
            id=r["id"],
            role=r["role"],
            content=r["content"],
            products=product_cards(_product_ids(r["products_json"])) if r["role"] == "assistant" else [],
            created_at=r["created_at"],
        )
        for r in rows
    ]


def history_turns(messages: list[SavedMessage]) -> list[ChatTurn]:
    """Saved messages in the shape the agent's message history uses."""
    return [
        ChatTurn(
            role=m.role,
            content=m.content[:4000],
            product_ids=[p.product_id for p in m.products],
            sent_at=m.created_at,
        )
        for m in messages
    ]


def save_exchange(user_id: int, question: str, reply: str, products: list[ProductSummary]) -> None:
    """Store one question and the assistant's answer (with its product cards) on the account."""
    with db(write=True) as conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'user', ?)", (user_id, question)
        )
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, 'assistant', ?, ?)",
            (user_id, reply, json.dumps([p.model_dump() for p in products])),
        )


def clear_history(user_id: int) -> int:
    with db(write=True) as conn:
        return conn.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,)).rowcount
