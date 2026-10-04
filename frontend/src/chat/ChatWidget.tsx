import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { formatPrice, searchHref } from '../api'
import DanAvatar from '../components/DanAvatar'
import { suggestionsFor } from './suggestions'
import { useChat } from './useChat'

export default function ChatWidget() {
  const chat = useChat()
  const [draft, setDraft] = useState('')
  const listRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const location = useLocation()
  const suggestions = suggestionsFor(location.pathname, location.search, chat.focusProduct !== null)
  // Show starter questions on an empty chat, and on product or search pages after that.
  const showSuggestions = !chat.isSending && (chat.messages.length === 0 || suggestions.pageSpecific)

  // Keep the newest message in view.
  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight })
  }, [chat.messages, chat.isSending, chat.isOpen])

  // Put the cursor in the box when the panel opens or a product is attached.
  useEffect(() => {
    if (chat.isOpen) inputRef.current?.focus()
  }, [chat.isOpen, chat.focusProduct])

  function submit(e?: FormEvent) {
    e?.preventDefault()
    if (!draft.trim()) return
    void chat.send(draft)
    setDraft('')
  }

  if (!chat.isOpen) {
    return (
      <button
        className="chat-launcher"
        onClick={chat.open}
        aria-label="Chat with Handsome Dan, the shopping assistant"
        title="Ask Handsome Dan"
      >
        <DanAvatar size={56} />
      </button>
    )
  }

  return (
    <aside className="chat-panel" aria-label="Handsome Dan, shopping assistant">
      <header className="chat-header">
        <DanAvatar size={40} className="chat-header-avatar" />
        <div className="chat-header-text">
          <p className="chat-title">Handsome Dan</p>
          <p className="chat-subtitle">
            {chat.savedToAccount
              ? 'Saved to your account'
              : 'Log in to save chats'}
          </p>
        </div>
        <div className="chat-header-actions">
          {chat.messages.length > 0 && (
            <button
              className="chat-clear"
              onClick={() => {
                const ok =
                  !chat.savedToAccount ||
                  window.confirm('Delete your saved chat history? This cannot be undone.')
                if (ok) void chat.clearChat()
              }}
            >
              Clear
            </button>
          )}
          <button className="chat-close" onClick={chat.close} aria-label="Close shopping assistant">
            ×
          </button>
        </div>
      </header>

      <div className="chat-messages" ref={listRef} aria-live="polite">
        {chat.messages.length === 0 && (
          <div className="chat-empty">
            <DanAvatar size={64} className="chat-empty-avatar" />
            <p>Handsome Dan here. What can I help you find?</p>
            <p className="chat-empty-hint">
              Pick a question below, type your own, or click <strong>Ask about this</strong> on any product.
            </p>
          </div>
        )}
        {chat.messages.map((m) => (
          <div key={m.id} className={`chat-row chat-row-${m.role}`}>
            {m.role === 'assistant' && <DanAvatar size={28} className="chat-msg-avatar" />}
            <div className={`chat-msg chat-msg-${m.role}${m.notice ? ' chat-msg-notice' : ''}`}>
              <p className="chat-msg-text">{m.content}</p>
              {m.products && m.products.length > 0 && (
                <ul className="chat-products">
                  {m.products.map((p) => (
                    <li key={p.product_id}>
                      <Link to={`/products/${p.product_id}`} className="chat-product">
                        <img src={p.image_url} alt="" />
                        <span>
                          <span className="chat-product-name">{p.name}</span>
                          <span className="chat-product-price">{formatPrice(p.price)}</span>
                          <span className="chat-product-info">{p.description}</span>
                        </span>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
              {m.pageSearch && (
                <Link to={searchHref(m.pageSearch)} className="chat-page-link">
                  {m.pageSearch.total === 1
                    ? 'View it on the page →'
                    : `View all ${m.pageSearch.total} on the page →`}
                </Link>
              )}
            </div>
          </div>
        ))}
        {chat.isSending && (
          <div className="chat-row chat-row-assistant">
            <DanAvatar size={28} className="chat-msg-avatar" />
            <div className="chat-msg chat-msg-assistant chat-typing">Handsome Dan is fetching that…</div>
          </div>
        )}
      </div>

      {showSuggestions && (
        <div className="chat-suggestions" aria-label="Suggested questions">
          {suggestions.questions.map((q) => (
            <button key={q} className="chat-chip" onClick={() => void chat.send(q)}>
              {q}
            </button>
          ))}
        </div>
      )}

      {chat.focusProduct && (
        <div className="chat-focus">
          <img src={chat.focusProduct.image_url} alt="" />
          <span>
            Asking about <strong>{chat.focusProduct.name}</strong>
          </span>
          <button onClick={chat.clearFocusProduct} aria-label="Stop asking about this product">
            ×
          </button>
        </div>
      )}

      <form className="chat-form" onSubmit={submit}>
        <textarea
          ref={inputRef}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) submit(e)
          }}
          placeholder="Type your question…"
          rows={2}
          maxLength={1000}
          aria-label="Message"
        />
        <button type="submit" className="btn btn-primary" disabled={!draft.trim() || chat.isSending}>
          Send
        </button>
      </form>
    </aside>
  )
}
