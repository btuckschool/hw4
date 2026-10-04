"""Campus Customs API.

Run from this folder with: uvicorn main:app --reload
"""

import hashlib
import hmac
import logging
import re
import secrets
import sqlite3
import time

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from pydantic_ai.exceptions import ContentFilterError, ModelHTTPError

from agent import AgentNotConfigured, run_chat
from models import (
    ChatDeps,
    ChatHistory,
    ChatRequest,
    ChatResponse,
    LoginRequest,
    PageSearchResult,
    ProductDetail,
    ProductFilters,
    ProductSummary,
    RegisterRequest,
    SearchPage,
    User,
)
from tools import (
    IMAGES_DIR,
    all_products,
    clear_history,
    db,
    history_turns,
    load_history,
    product_cards,
    product_detail,
    save_exchange,
    search_catalogue,
)

log = logging.getLogger("campus_customs")

app = FastAPI(title="Campus Customs API")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


# ---------- Products ----------


@app.get("/api/products", response_model=list[ProductSummary])
def list_products() -> list[ProductSummary]:
    return all_products()


@app.get("/api/search", response_model=SearchPage)
def search(filters: ProductFilters = Depends()) -> SearchPage:
    # Same matching rules as the agent's search tool (navy/blue, hoodie grouping, keywords).
    products = search_catalogue(filters)
    return SearchPage(total=len(products), products=products)


@app.get("/api/products/{product_id}", response_model=ProductDetail)
def get_product(product_id: str) -> ProductDetail:
    product = product_detail(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# ---------- Password hashing ----------

# New hashes: pbkdf2_sha256$<iterations>$<salt>$<hex digest>, at OWASP's recommended
# iteration count. The seeded accounts use the older pbkdf2_sha256$<salt>$<hex digest>
# format, which was made with 120,000 iterations; both are verified.
HASH_ALGORITHM = "pbkdf2_sha256"
HASH_ITERATIONS = 600_000
LEGACY_ITERATIONS = 120_000


def _pbkdf2(password: str, salt: str, iterations: int) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    return f"{HASH_ALGORITHM}${HASH_ITERATIONS}${salt}${_pbkdf2(password, salt, HASH_ITERATIONS)}"


def verify_password(password: str, stored: str) -> bool:
    parts = stored.split("$")
    if len(parts) == 4 and parts[0] == HASH_ALGORITHM and parts[1].isdigit():
        _, iterations, salt, digest = parts
        candidate = _pbkdf2(password, salt, int(iterations))
    elif len(parts) == 3 and parts[0] == HASH_ALGORITHM:
        _, salt, digest = parts
        candidate = _pbkdf2(password, salt, LEGACY_ITERATIONS)
    else:
        return False
    # Constant-time comparison so response timing doesn't leak how close a guess was.
    return hmac.compare_digest(candidate, digest)


# Used when the email doesn't exist, so a login takes the same time either way and
# can't be used to discover which emails have accounts.
_DUMMY_HASH = hash_password(secrets.token_hex(16))


# ---------- Sessions ----------

# Server-side sessions: the browser only holds a random token in an HttpOnly cookie.
# Sessions live in memory, so restarting the server signs everyone out.
SESSION_COOKIE = "cc_session"
SESSION_SECONDS = 7 * 24 * 60 * 60
_sessions: dict[str, tuple[int, float]] = {}  # token -> (user_id, expires_at)

# Simple brute-force protection: too many wrong passwords for one email locks it briefly.
MAX_FAILED_LOGINS = 5
LOCKOUT_SECONDS = 15 * 60
_failed_logins: dict[str, list[float]] = {}  # email -> timestamps of recent failures


def start_session(response: Response, request: Request, user_id: int) -> None:
    token = secrets.token_urlsafe(32)
    _sessions[token] = (user_id, time.time() + SESSION_SECONDS)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_SECONDS,
        httponly=True,  # not readable by page JavaScript
        samesite="lax",  # not sent on cross-site form posts
        secure=request.url.scheme == "https",
    )


def session_user_id(request: Request) -> int | None:
    token = request.cookies.get(SESSION_COOKIE)
    session = _sessions.get(token) if token else None
    if session is None:
        return None
    user_id, expires_at = session
    if expires_at < time.time():
        _sessions.pop(token, None)
        return None
    return user_id


def recent_failures(email: str) -> list[float]:
    cutoff = time.time() - LOCKOUT_SECONDS
    failures = [t for t in _failed_logins.get(email, []) if t > cutoff]
    _failed_logins[email] = failures
    return failures


def row_to_user(row: sqlite3.Row) -> User:
    return User(id=row["id"], first_name=row["first_name"], last_name=row["last_name"], email=row["email"])


# ---------- Accounts ----------

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD = 8
MAX_PASSWORD = 128  # caps hashing cost per request


def normalize_email(email: str) -> str:
    return email.strip().lower()


@app.post("/api/auth/register", response_model=User, status_code=201)
def register(body: RegisterRequest, request: Request, response: Response) -> User:
    first, last = body.first_name.strip(), body.last_name.strip()
    email = normalize_email(body.email)

    if not first or not last:
        raise HTTPException(400, "First and last name are required.")
    if len(first) > 50 or len(last) > 50:
        raise HTTPException(400, "Names must be 50 characters or fewer.")
    if not EMAIL_RE.match(email) or len(email) > 254:
        raise HTTPException(400, "Please enter a valid email address.")
    if not MIN_PASSWORD <= len(body.password) <= MAX_PASSWORD:
        raise HTTPException(400, f"Password must be {MIN_PASSWORD} to {MAX_PASSWORD} characters.")
    if body.password != body.confirm_password:
        raise HTTPException(400, "Passwords do not match.")

    try:
        with db(write=True) as conn:
            cur = conn.execute(
                "INSERT INTO users (name, email, password_hash, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
                (f"{first} {last}", email, hash_password(body.password), first, last),
            )
            user_id = cur.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(409, "An account with that email already exists.")

    start_session(response, request, user_id)
    return User(id=user_id, first_name=first, last_name=last, email=email)


@app.post("/api/auth/login", response_model=User)
def login(body: LoginRequest, request: Request, response: Response) -> User:
    email = normalize_email(body.email)
    if len(recent_failures(email)) >= MAX_FAILED_LOGINS:
        raise HTTPException(429, "Too many failed attempts. Please wait 15 minutes and try again.")

    with db() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    password = body.password[:MAX_PASSWORD]
    valid = verify_password(password, row["password_hash"] if row else _DUMMY_HASH) and row is not None
    if not valid:
        _failed_logins.setdefault(email, []).append(time.time())
        # Same message whether the email or the password was wrong.
        raise HTTPException(401, "Incorrect email or password.")

    _failed_logins.pop(email, None)
    start_session(response, request, row["id"])
    return row_to_user(row)


@app.post("/api/auth/logout", status_code=204)
def logout(request: Request, response: Response) -> None:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        _sessions.pop(token, None)
    response.delete_cookie(SESSION_COOKIE)


@app.get("/api/auth/me", response_model=User | None)
def me(request: Request) -> User | None:
    user_id = session_user_id(request)
    if user_id is None:
        return None
    with db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return row_to_user(row) if row else None


# ---------- Chat ----------

# Shown when the provider's content filter blocks a message. The filter doesn't say why, and it
# also blocks messages from people in crisis, so this reply never pushes products and always
# includes crisis resources.
CONTENT_FILTER_REPLY = (
    "I'm not able to respond to that message. If you're going through something difficult or "
    "anyone is in danger, please call 911, or call or text 988 to reach the Suicide & Crisis "
    "Lifeline. If you're shopping for Yale apparel, I'm happy to help with that anytime."
)

# Per-visitor rate limit so one browser can't run up model costs.
CHAT_LIMIT = 20
CHAT_WINDOW_SECONDS = 60
_chat_times: dict[str, list[float]] = {}


def check_chat_rate(request: Request) -> None:
    key = request.cookies.get(SESSION_COOKIE) or (request.client.host if request.client else "unknown")
    now = time.time()
    recent = [t for t in _chat_times.get(key, []) if t > now - CHAT_WINDOW_SECONDS]
    if len(recent) >= CHAT_LIMIT:
        raise HTTPException(429, "You're sending messages quickly. Please wait a moment and try again.")
    recent.append(now)
    _chat_times[key] = recent


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request) -> ChatResponse:
    check_chat_rate(request)
    message = body.message.strip()
    user = me(request)

    # Who is chatting comes from the session cookie, never from the request body.
    # Logged-in shoppers' history comes from their account; guests send theirs from the tab.
    if user:
        history = history_turns(load_history(user.id))
    else:
        history = body.history

    page = body.page
    page_product = product_detail(page.product_id) if page and page.product_id else None
    if page and page.product_id and page_product is None:
        page = page.model_copy(update={"product_id": None})
    focus = body.product_id if body.product_id and product_detail(body.product_id) else None

    deps = ChatDeps(
        user_id=user.id if user else None,
        first_name=user.first_name if user else None,
        last_name=user.last_name if user else None,
        email=user.email if user else None,
        focus_product_id=focus,
        page=page,
        page_product_name=page_product.name if page_product else None,
    )
    try:
        reply = await run_chat(message, history, deps, history_source="account" if user else "browser")
    except (ModelHTTPError, ContentFilterError) as exc:
        # The model provider's own safety filter blocked the message (for example a jailbreak
        # attempt). Answer politely instead of showing an error.
        body = str(getattr(exc, "body", exc))
        if isinstance(exc, ContentFilterError) or "content management policy" in body or "content_filter" in body:
            log.warning("Chat message blocked by provider content filter")
            response = ChatResponse(reply=CONTENT_FILTER_REPLY, products=[])
            if user:
                save_exchange(user.id, message, response.reply, [])
                response.saved = True
            return response
        log.exception("Chat model request failed")
        raise HTTPException(502, "The shopping assistant ran into a problem. Please try again.")
    except AgentNotConfigured as exc:
        log.error("Chat agent not configured: %s", exc)
        raise HTTPException(503, "The shopping assistant isn't set up yet.")
    except Exception:
        log.exception("Chat agent failed")
        raise HTTPException(502, "The shopping assistant ran into a problem. Please try again.")

    # Cards are rebuilt from the database, so only real products with real prices are shown.
    response = ChatResponse(reply=reply.reply.strip(), products=product_cards(reply.product_ids))

    # Re-run the agent's page search here, and only send it on if it finds something,
    # so the page never switches to an empty or made-up result list.
    if reply.page_search:
        total = len(search_catalogue(reply.page_search.filters))
        if total > 0:
            response.page_search = PageSearchResult(
                title=reply.page_search.title.strip() or "Search results",
                filters=reply.page_search.filters,
                total=total,
            )

    if user:
        save_exchange(user.id, message, response.reply, response.products)
        response.saved = True
    return response


@app.get("/api/chat/history", response_model=ChatHistory)
def get_chat_history(request: Request) -> ChatHistory:
    """The logged-in shopper's saved conversation. Guests have none."""
    user = me(request)
    return ChatHistory(messages=load_history(user.id) if user else [])


@app.delete("/api/chat/history", status_code=204)
def delete_chat_history(request: Request) -> None:
    """Lets a logged-in shopper erase their saved conversation."""
    user = me(request)
    if user is None:
        raise HTTPException(401, "Log in to manage your chat history.")
    clear_history(user.id)


app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")
