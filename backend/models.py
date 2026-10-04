"""Pydantic models shared by the API and the chat agent."""

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field

# ---------- Products ----------


class SizeStock(BaseModel):
    size: str
    quantity: int


class ProductSummary(BaseModel):
    """A product card: what the Products grid and chat replies show for each item."""

    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]
    price: float
    image_url: str
    in_stock: bool


class ProductDetail(ProductSummary):
    search_tags: list[str]
    sizes: list[SizeStock]
    total_stock: int


# ---------- Accounts ----------


class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    confirm_password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class User(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str


# ---------- Agent lookup results ----------
# What the agent's tools return. Every value is read from the database at call time,
# and the field names say exactly what each value means, so the model has no reason to guess.

StockStatus = Literal["in_stock", "some_sizes_sold_out", "sold_out"]


class SizeAvailability(BaseModel):
    size: str = Field(description="XS, S, M, L, XL or XXL.")
    quantity: int = Field(description="Units on hand right now.")
    in_stock: bool = Field(description="False means this size is out of stock.")


class ProductInfo(BaseModel):
    """Everything the agent may say about one product."""

    product_id: str = Field(description="Use this ID for product cards and follow-up lookups.")
    name: str
    category: str = Field(description="Shopper-facing group, e.g. hoodie or crewneck.")
    garment_type: str = Field(description="The catalogue's exact garment label.")
    price: float = Field(description="Current price in US dollars. Quote it exactly.")
    description: str | None = Field(description="Full description, or null if none is on file.")
    design_colors: list[str] = Field(
        description="Colors in the product's single design. Not a list of colorway options."
    )
    stock_status: StockStatus = Field(
        description="in_stock = every size available; some_sizes_sold_out; sold_out = no sizes left."
    )
    total_stock: int = Field(description="Units on hand across all sizes.")
    sizes: list[SizeAvailability] = Field(description="Stock for every size, XS to XXL.")


class ProductBrief(BaseModel):
    """A compact product summary for lists (search results, similar items).

    Lists can hold a dozen products, and the model re-reads every tool result on each call,
    so list entries carry only what's needed to compare and recommend. Full descriptions and
    per-size quantities come from get_product_details or check_stock.
    """

    product_id: str
    name: str
    category: str
    price: float
    design_colors: list[str]
    stock_status: StockStatus
    sizes_in_stock: list[str] = Field(description="Sizes with at least one unit on hand.")


class ProductLookup(BaseModel):
    """Result of looking up one product by ID."""

    found: bool
    product: ProductInfo | None = None
    message: str | None = Field(default=None, description="Explains why nothing was found.")


class StockCheck(BaseModel):
    """Result of checking whether a product is available, optionally in one size."""

    found: bool
    product_id: str
    name: str | None = None
    price: float | None = None
    requested_size: str | None = None
    requested_size_quantity: int | None = Field(
        default=None, description="Units on hand in the requested size; 0 means out of stock."
    )
    requested_size_in_stock: bool | None = None
    stock_status: StockStatus | None = None
    sizes_in_stock: list[str] = Field(default_factory=list)
    sizes_out_of_stock: list[str] = Field(default_factory=list)
    message: str = Field(description="One-line plain summary of the result, safe to relay.")


class NamedProduct(BaseModel):
    """Result of find_product: a product looked up by name, with its stock, in one step."""

    found: bool
    query: str
    product: ProductInfo | None = Field(default=None, description="Full facts for the best match.")
    requested_size: str | None = None
    requested_size_quantity: int | None = Field(
        default=None, description="Units on hand in the requested size; 0 means out of stock."
    )
    requested_size_in_stock: bool | None = None
    other_close_matches: list[ProductBrief] = Field(
        default_factory=list,
        description="Other products with similar names, in case the shopper meant one of these.",
    )
    message: str = Field(description="One-line plain summary of the result, safe to relay.")


class SearchResults(BaseModel):
    """Result of a catalogue search."""

    total_matches: int = Field(description="How many products matched, before the limit.")
    returned: int = Field(description="How many products are in this result.")
    filters_used: dict[str, str | float] = Field(description="The filters the search applied.")
    products: list[ProductBrief]
    out_of_stock_in_requested_size: list[ProductBrief] = Field(
        default_factory=list,
        description=(
            "Products that matched everything except size_in_stock: they exist but are out of "
            "stock in that size. Tell the shopper instead of substituting another product."
        ),
    )


class SimilarProducts(BaseModel):
    """Products similar to one product. Only items with stock are included."""

    found: bool
    similar_to: str
    products: list[ProductBrief] = Field(default_factory=list)
    message: str | None = None


class CategorySummary(BaseModel):
    category: str
    product_count: int
    products_with_stock: int
    min_price: float
    max_price: float


class CatalogueOverview(BaseModel):
    """What the store carries, by category."""

    total_products: int
    sizes_offered: list[str]
    categories: list[CategorySummary]


# ---------- Page search (chat results shown on the Products page) ----------


class ProductFilters(BaseModel):
    """The same filters search_products takes. Used to show a search's results on the page."""

    keywords: str | None = None
    category: str | None = None
    color: str | None = None
    size_in_stock: str | None = None
    min_price: float | None = None
    max_price: float | None = None


class PageSearch(BaseModel):
    """The agent's request to show a search's full results as product cards on the page."""

    title: str = Field(
        max_length=60,
        description='A short heading for the results, e.g. "T-shirts" or "Navy hoodies under $70".',
    )
    filters: ProductFilters = Field(
        description="Exactly the filters of the search_products call whose results you're describing."
    )


class SearchPage(BaseModel):
    """What GET /api/search returns: every product matching the filters."""

    total: int
    products: list[ProductSummary]


# ---------- Chat ----------

MAX_MESSAGE_CHARS = 1000
MAX_HISTORY_TURNS = 20


class ChatTurn(BaseModel):
    """One earlier message in the conversation."""

    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)
    # Products shown as cards with an assistant message, so "the first one" can be resolved.
    product_ids: list[str] = Field(default_factory=list, max_length=12)
    # When it was sent (UTC), for saved history only, so "earlier today" or "last week" make sense.
    sent_at: str | None = None


PageKind = Literal["home", "products", "search", "product", "about", "login", "create-account", "other"]


class PageContext(BaseModel):
    """Which page the shopper is looking at when they send a message."""

    path: str = Field(default="/", max_length=300)
    kind: PageKind = "other"
    # On a product page: the product shown.
    product_id: str | None = None
    # On search results shown from the chat: the heading and filters.
    search_title: str | None = Field(default=None, max_length=60)
    search_filters: ProductFilters | None = None


class ChatRequest(BaseModel):
    """What the chat widget sends to POST /api/chat."""

    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)
    # Guests only: logged-in shoppers' history is loaded from the database instead.
    history: list[ChatTurn] = Field(default_factory=list)
    # Set when the shopper clicked "Ask about this" on a product.
    product_id: str | None = None
    page: PageContext | None = None


class ChatReply(BaseModel):
    """The agent's structured output: its answer plus the products to show as cards."""

    reply: str = Field(description="The answer to show the shopper, in plain text (no Markdown).")
    product_ids: list[str] = Field(
        default_factory=list,
        max_length=6,
        description=(
            "IDs of products to show as cards under the reply, most relevant first. Only use IDs "
            "returned by a tool in this conversation. Leave empty when no product is relevant."
        ),
    )
    page_search: PageSearch | None = Field(
        default=None,
        description=(
            "Set when the shopper is browsing a kind of item (a category, color, style, school "
            "or price range) and the search found products: the website then shows every match "
            "as product cards on the Products page. Leave null for greetings, questions about one "
            "product, stock checks and searches that found nothing."
        ),
    )


class PageSearchResult(BaseModel):
    """A page search the backend has checked: the site shows these filters on the Products page."""

    title: str
    filters: ProductFilters
    total: int


class ChatResponse(BaseModel):
    """What POST /api/chat returns to the chat widget."""

    reply: str
    products: list[ProductSummary]
    page_search: PageSearchResult | None = None
    saved: bool = Field(default=False, description="True when the exchange was saved to the account.")


class SavedMessage(BaseModel):
    """One message from a logged-in shopper's saved chat history."""

    id: int
    role: Literal["user", "assistant"]
    content: str
    products: list[ProductSummary]
    created_at: str


class ChatHistory(BaseModel):
    """What GET /api/chat/history returns."""

    messages: list[SavedMessage]


class CustomerProfile(BaseModel):
    """What the agent may know about the person chatting. Guests get logged_in=False and nothing else."""

    logged_in: bool
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    member_since: str | None = Field(default=None, description="Account creation date (YYYY-MM-DD).")
    saved_messages: int | None = Field(default=None, description="Messages saved in their chat history.")


@dataclass
class ChatDeps:
    """Per-request context handed to the agent and its tools.

    Customer fields are filled only for logged-in shoppers, from the session cookie on the
    server, never from anything the browser claims.
    """

    user_id: int | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    focus_product_id: str | None = None
    page: PageContext | None = None
    page_product_name: str | None = None
