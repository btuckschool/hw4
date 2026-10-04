"""The Campus Customs chat agent: prompt file + model + tools, wired with PydanticAI."""

import fcntl
import json
import logging
import os
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import (
    ContentFilterError,
    ModelAPIError,
    ModelHTTPError,
    UnexpectedModelBehavior,
    UsageLimitExceeded,
)
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    RetryPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings
from pydantic_ai.usage import UsageLimits

from models import MAX_HISTORY_TURNS, ChatDeps, ChatReply, ChatTurn
from tools import AGENT_TOOLS

BACKEND_DIR = Path(__file__).resolve().parent
PROMPT_PATH = BACKEND_DIR / "prompts" / "prompt.md"
AUDIT_PATH = Path(os.environ.get("CAMPUS_CUSTOMS_AUDIT", BACKEND_DIR.parent / "output" / "audit_trail.json"))

# Agent-loop limits (see "Specs" in output/harness.md).
REQUEST_LIMIT = 8  # model round trips per question
MAX_COMPLETION_TOKENS = 2000  # per model call
OUTPUT_RETRIES = 2  # re-asks when the output doesn't match ChatReply
MODEL_TIMEOUT_SECONDS = 60

# Use the nearest .env: HW4/.env if present, otherwise the class folder's shared one.
for folder in [BACKEND_DIR, *BACKEND_DIR.parents]:
    if (folder / ".env").is_file():
        load_dotenv(folder / ".env")
        break

PORTKEY_BASE_URL = "https://api.portkey.ai/v1"
MODEL_NAME = os.environ.get("CAMPUS_CUSTOMS_MODEL", "gpt-5.6-luna")


class AgentNotConfigured(RuntimeError):
    pass


def build_model() -> OpenAIChatModel:
    """OpenAI's Luna model, reached through the Portkey gateway."""
    portkey_key = os.environ.get("PORTKEY_API_KEY")
    if not portkey_key:
        raise AgentNotConfigured("PORTKEY_API_KEY is not set. Add it to the .env file.")
    client = AsyncOpenAI(
        base_url=PORTKEY_BASE_URL,
        # Portkey holds the OpenAI credential; the SDK just needs a non-empty value here.
        api_key="portkey",
        default_headers={
            "x-portkey-api-key": portkey_key,
            "x-portkey-provider": "openai",
            # Portkey's firewall rejects the default Python user agent.
            "User-Agent": "campus-customs-hw4/1.0",
        },
        timeout=MODEL_TIMEOUT_SECONDS,
    )
    return OpenAIChatModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))


@lru_cache
def get_agent() -> Agent[ChatDeps, ChatReply]:
    agent = Agent(
        build_model(),
        deps_type=ChatDeps,
        output_type=ChatReply,
        tools=AGENT_TOOLS,
        # Sent to OpenAI as max_completion_tokens.
        model_settings=ModelSettings(max_tokens=MAX_COMPLETION_TOKENS),
        retries=OUTPUT_RETRIES,
    )

    @agent.instructions
    def system_prompt() -> str:
        # Read on every run, so edits to prompt.md apply without restarting the server.
        return PROMPT_PATH.read_text(encoding="utf-8")

    @agent.instructions
    def shopper_context(ctx: RunContext[ChatDeps]) -> str:
        return describe_context(ctx.deps)

    return agent


def describe_context(deps: ChatDeps) -> str:
    """The per-request facts the agent gets: who is chatting and what they're looking at."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    lines = ["## This conversation", "", f"Current time: {now} UTC.", "", "### Who is chatting"]
    if deps.user_id is not None:
        lines.append(
            f"The shopper is logged in as {deps.first_name} {deps.last_name} ({deps.email}). "
            "Their earlier conversations are saved to their account and included above."
        )
    else:
        lines.append(
            "The shopper is a guest (not logged in). You don't know their name or email, and "
            "this conversation won't be saved after they leave."
        )

    lines += ["", "### What they're looking at"]
    page = deps.page
    if page is None:
        lines.append("Unknown.")
    elif page.kind == "product" and page.product_id:
        lines.append(
            f'They are on the product page for "{deps.page_product_name}" (product_id "{page.product_id}").'
        )
    elif page.kind == "search":
        title = page.search_title or "search results"
        filters = page.search_filters.model_dump(exclude_none=True) if page.search_filters else {}
        lines.append(f'They are viewing search results titled "{title}" (filters: {filters}).')
    else:
        lines.append(f"They are on the {page.kind.replace('-', ' ')} page ({page.path}).")

    if deps.focus_product_id:
        lines.append(f'They clicked "Ask about this" on product_id "{deps.focus_product_id}".')

    lines += ["", "### What \"this\" means right now"]
    if deps.focus_product_id:
        lines.append(f'"This", "it" and "this one" mean product_id "{deps.focus_product_id}" (the "Ask about this" product).')
    elif page is not None and page.kind == "product" and page.product_id:
        lines.append(f'"This", "it" and "this one" mean product_id "{page.product_id}" (the product page they\'re on).')
    else:
        lines.append(
            '"This" isn\'t tied to a page product. Use the most recent product discussed in the '
            "conversation; if that's unclear, ask which product they mean."
        )

    return "\n".join(lines)


def to_message_history(history: list[ChatTurn]) -> list[ModelMessage]:
    """Turn the browser's plain chat log into PydanticAI messages (most recent turns only)."""
    turns = history[-MAX_HISTORY_TURNS:]
    while turns and turns[0].role != "user":  # history must start with a shopper message
        turns = turns[1:]
    messages: list[ModelMessage] = []
    for turn in turns:
        if turn.role == "user":
            content = f"[Sent {turn.sent_at} UTC] {turn.content}" if turn.sent_at else turn.content
            messages.append(ModelRequest(parts=[UserPromptPart(content=content)]))
        else:
            content = turn.content
            if turn.product_ids:
                # Lets the agent resolve "the first one" or "that hoodie" in later questions.
                content += f"\n\n[Product cards shown with this reply: {', '.join(turn.product_ids)}]"
            messages.append(ModelResponse(parts=[TextPart(content=content)]))
    return messages


# ---------- Crisis safety net ----------
# Messages about self-harm or immediate danger get a fixed, caring reply with crisis resources
# without going to the model. That way the answer never depends on the model, and never
# depends on the provider's content filter (which blocks these messages and would otherwise
# lead to a generic refusal).

_CRISIS = re.compile(
    r"\b(suicid\w*|kill(ing)? my ?self|hurt(ing)? my ?self|harm(ing)? my ?self|self[- ]?harm"
    r"|end(ing)? (it all|my life)|want(ed)? to die|don'?t want to (live|be alive|be here)"
    r"|no (point|reason) (in )?(living|going on|anymore)|better off dead"
    r"|(i'?m|i am) in danger|someone is (hurting|abusing|threatening) me)\b",
    re.IGNORECASE,
)

CRISIS_REPLY = (
    "I'm really sorry you're going through this, and I'm glad you told me. You deserve support "
    "right now from someone who can really help. If you're in the US, you can call or text 988 "
    "to reach the Suicide & Crisis Lifeline any time, day or night. If you're in immediate danger, "
    "please call 911 or your local emergency number. If you can, reach out to someone you trust "
    "and let them know how you're feeling."
)


def is_crisis(message: str) -> bool:
    return bool(_CRISIS.search(message))


# ---------- Audit trail ----------
# Every agent run is appended to output/audit_trail.json: when it ran, who (guest or user ID),
# which tools were called with what, what they returned (summarized), the final answer, token
# usage and why the loop stopped. The file is a JSON array that only ever grows: each entry is
# written in just before the closing bracket, so earlier entries are never rewritten or wiped.

_audit_lock = threading.Lock()
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_LONG_NUMBER = re.compile(r"\b\d(?:[ -]?\d){11,18}\b")  # card-like numbers
_PHONE = re.compile(r"\(?\b\d{3}\)?[ .-]?\d{3}[ .-]?\d{4}\b")


def redact(text: str, limit: int = 400) -> str:
    """Keep personal data out of the log: emails and card-like numbers are masked."""
    text = _EMAIL.sub("[email removed]", text)
    text = _PHONE.sub("[phone removed]", _LONG_NUMBER.sub("[number removed]", text))
    return text if len(text) <= limit else text[:limit] + "…"


_PRODUCT_KEYS = ("product_id", "price", "stock_status", "sizes_in_stock", "total_stock")


def summarize_result(value: Any) -> Any:
    """Shrink a tool result for the log: scalars kept, each product reduced to its key facts."""
    if isinstance(value, BaseModel):
        value = value.model_dump()
    if isinstance(value, dict):
        # Product records (ProductInfo / ProductBrief) shrink to key facts; result wrappers such as
        # StockCheck keep every field, since those are the answer.
        if "product_id" in value and "category" in value:
            return {k: value[k] for k in _PRODUCT_KEYS if k in value}
        return {k: summarize_result(v) for k, v in value.items() if v not in (None, [], {})}
    if isinstance(value, list):
        return [summarize_result(v) for v in value[:12]]
    if isinstance(value, str):
        return redact(value, 300)
    return value


def _steps(messages: list[ModelMessage]) -> tuple[list[dict], list[str]]:
    steps: list[dict] = []
    tools_used: list[str] = []
    for m in messages:
        if isinstance(m, ModelResponse):
            calls = [p for p in m.parts if isinstance(p, ToolCallPart)]
            step: dict = {"type": "model_response", "finish_reason": m.finish_reason}
            tool_calls = [
                {"tool": c.tool_name, "args": summarize_result(c.args_as_dict())}
                for c in calls
                if c.tool_name != "final_result"
            ]
            if tool_calls:
                step["tool_calls"] = tool_calls
                tools_used += [c["tool"] for c in tool_calls]
            if any(c.tool_name == "final_result" for c in calls):
                step["final_answer"] = True
            steps.append(step)
        elif isinstance(m, ModelRequest):
            results = [
                {"tool": p.tool_name, "result": summarize_result(p.content)}
                for p in m.parts
                if isinstance(p, ToolReturnPart) and p.tool_name != "final_result"
            ]
            retries = [p for p in m.parts if isinstance(p, RetryPromptPart)]
            if results:
                steps.append({"type": "tool_results", "results": results})
            if retries:
                steps.append({"type": "retry", "count": len(retries)})
    return steps, tools_used


def stop_reason_for(exc: BaseException | None) -> str:
    if exc is None:
        return "final_result"
    if isinstance(exc, ContentFilterError) or (
        isinstance(exc, ModelHTTPError)
        and ("content management policy" in str(exc.body) or "content_filter" in str(exc.body))
    ):
        return "provider_content_filter"
    if isinstance(exc, UsageLimitExceeded):
        return "request_limit_reached"
    if isinstance(exc, UnexpectedModelBehavior):
        return "invalid_output"
    if isinstance(exc, AgentNotConfigured):
        return "not_configured"
    if isinstance(exc, (ModelHTTPError, ModelAPIError)):
        return "model_error"
    return "error"


def append_audit(entry: dict) -> None:
    line = json.dumps(entry, ensure_ascii=False, default=str).encode()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _audit_lock, open(AUDIT_PATH, "a+b") as f:
        fcntl.flock(f, fcntl.LOCK_EX)  # also guards against other processes writing at once
        f.seek(0, os.SEEK_END)
        size = f.tell()
        if size == 0:
            f.write(b"[\n  " + line + b"\n]\n")
            return
        f.seek(max(0, size - 4096))
        tail = f.read()
        close = tail.rfind(b"]")
        if close == -1:  # not a JSON array we recognize: never overwrite it, just add the entry
            f.write(b"\n" + line + b"\n")
            return
        before = tail[:close].rstrip()
        separator = b"\n  " if before.endswith(b"[") else b",\n  "
        f.truncate(size - len(tail) + len(before))  # removes only the closing "]" and whitespace
        f.write(separator + line + b"\n]\n")


async def run_chat(
    message: str, history: list[ChatTurn], deps: ChatDeps, history_source: str = "browser"
) -> ChatReply:
    """Run the agent loop for one question and record it in the audit trail."""
    started = time.time()
    entry: dict = {
        "id": uuid.uuid4().hex[:12],
        "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": MODEL_NAME,
        "shopper": f"user:{deps.user_id}" if deps.user_id is not None else "guest",
        "page": {"kind": deps.page.kind, "product_id": deps.page.product_id} if deps.page else None,
        "focus_product_id": deps.focus_product_id,
        "history_turns": min(len(history), MAX_HISTORY_TURNS),
        "history_source": history_source,
        "message": redact(message),
    }
    run = None
    error: BaseException | None = None
    if is_crisis(message):
        entry.update(
            {
                "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "duration_ms": round((time.time() - started) * 1000),
                "tools_used": [],
                "steps": [],
                "usage": {"model_requests": 0, "input_tokens": 0, "output_tokens": 0},
                "final": {"reply": CRISIS_REPLY, "product_ids": [], "page_search": None},
                "stop_reason": "crisis_safety_reply",
            }
        )
        append_audit(entry)
        return ChatReply(reply=CRISIS_REPLY)
    try:
        async with get_agent().iter(
            message,
            message_history=to_message_history(history),
            deps=deps,
            # Caps model round trips per question so a confused run can't loop forever.
            usage_limits=UsageLimits(request_limit=REQUEST_LIMIT),
        ) as run:
            async for _ in run:
                pass
        output: ChatReply = run.result.output
        entry["final"] = {
            "reply": redact(output.reply),
            "product_ids": output.product_ids,
            "page_search": output.page_search.model_dump(exclude_none=True) if output.page_search else None,
        }
        return output
    except BaseException as exc:
        error = exc
        raise
    finally:
        messages = run.new_messages() if run is not None else []
        steps, tools_used = _steps(messages)
        usage = run.usage() if run is not None and callable(run.usage) else (run.usage if run else None)
        entry.update(
            {
                "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "duration_ms": round((time.time() - started) * 1000),
                "tools_used": tools_used,
                "steps": steps,
                "usage": {
                    "model_requests": usage.requests,
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                }
                if usage
                else None,
                "stop_reason": stop_reason_for(error),
            }
        )
        if error is not None:
            entry["error"] = redact(f"{type(error).__name__}: {error}", 300)
        try:
            append_audit(entry)
        except OSError:
            # The audit trail must never break the chat, but a failure to write it is worth knowing.
            logging.getLogger("campus_customs").exception("Could not write the audit trail")
