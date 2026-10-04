import { useEffect, useRef, useState, type ReactNode } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { filtersFromParams, searchHref, type PageSearchResult, type ProductSummary } from '../api'
import { useAuth } from '../auth/useAuth'
import { ChatContext, type ChatMessage, type ChatState } from './context'

// Guests: sessionStorage keeps the conversation while they move between pages (and through a
// refresh) and drops it when they close the tab. Logged-in shoppers: the conversation is saved
// to their account by the backend and reloaded from there, so it isn't kept in the browser.
const STORAGE_KEY = 'campus-customs-chat'

interface Stored {
  messages: ChatMessage[]
  isOpen: boolean
  focusProduct: ProductSummary | null
}

function loadStored(): Stored {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw) as Stored
  } catch {
    // Ignore unreadable storage and start fresh.
  }
  return { messages: [], isOpen: false, focusProduct: null }
}

const newId = () => crypto.randomUUID()

interface SavedMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  products: ProductSummary[]
}

// Describes the page the shopper is on, so the assistant knows what "this" refers to.
function pageContext(pathname: string, search: string) {
  const product = pathname.match(/^\/products\/([^/]+)$/)
  if (product) return { path: pathname, kind: 'product', product_id: decodeURIComponent(product[1]) }
  if (pathname === '/products') {
    const params = new URLSearchParams(search)
    const filters = filtersFromParams(params)
    if (filters) {
      return {
        path: pathname + search,
        kind: 'search',
        search_title: params.get('title'),
        search_filters: Object.fromEntries(filters),
      }
    }
    return { path: pathname, kind: 'products' }
  }
  const kinds: Record<string, string> = {
    '/': 'home',
    '/about': 'about',
    '/login': 'login',
    '/create-account': 'create-account',
  }
  return { path: pathname, kind: kinds[pathname] ?? 'other' }
}

export function ChatProvider({ children }: { children: ReactNode }) {
  const { user, ready } = useAuth()
  const [initial] = useState(loadStored)
  const [messages, setMessages] = useState<ChatMessage[]>(initial.messages)
  const [isOpen, setIsOpen] = useState(initial.isOpen)
  const [focusProduct, setFocusProduct] = useState<ProductSummary | null>(initial.focusProduct)
  const [isSending, setIsSending] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const userId = user?.id ?? null
  const previousUserId = useRef<number | null | undefined>(undefined)
  // Which account the screen currently belongs to, so a reply that arrives after logging out
  // (or switching accounts) isn't shown to the next person.
  const sessionOwner = useRef<number | null>(userId)
  useEffect(() => {
    sessionOwner.current = userId
  }, [userId])

  // Keep guests' conversations in this tab only.
  useEffect(() => {
    const stored: Stored = { messages: userId ? [] : messages, isOpen, focusProduct }
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(stored))
  }, [messages, isOpen, focusProduct, userId])

  // Logging in loads the account's saved conversation; logging out clears the screen so the
  // next person at this computer doesn't see it.
  useEffect(() => {
    if (!ready) return
    const before = previousUserId.current
    previousUserId.current = userId
    if (userId === null) {
      if (before) {
        setMessages([])
        setFocusProduct(null)
      }
      return
    }
    let active = true
    fetch('/api/chat/history')
      .then((res) => (res.ok ? (res.json() as Promise<{ messages: SavedMessage[] }>) : { messages: [] }))
      .then((data) => {
        if (!active) return
        setMessages(
          data.messages.map((m) => ({
            id: `saved-${m.id}`,
            role: m.role,
            content: m.content,
            products: m.products,
          })),
        )
      })
      .catch(() => {})
    return () => {
      active = false
    }
  }, [ready, userId])

  async function send(text: string) {
    const content = text.trim()
    if (!content || isSending) return

    // Guests send their history from this tab; logged-in history is loaded on the server.
    const history = userId
      ? []
      : messages
          .filter((m) => !m.notice)
          .map(({ role, content, products }) => ({
            role,
            content,
            product_ids: (products ?? []).map((p) => p.product_id),
          }))
    setMessages((prev) => [...prev, { id: newId(), role: 'user', content }])
    setIsSending(true)
    const owner = userId

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: content,
          history,
          product_id: focusProduct?.product_id ?? null,
          page: pageContext(location.pathname, location.search),
        }),
      })
      if (!res.ok) {
        // Show the server's own message for expected problems (rate limit, not configured).
        const data = (await res.json().catch(() => null)) as { detail?: unknown } | null
        throw new Error(typeof data?.detail === 'string' ? data.detail : '')
      }
      const data = (await res.json()) as {
        reply: string
        products?: ProductSummary[]
        page_search?: PageSearchResult | null
      }
      if (sessionOwner.current !== owner) return
      const pageSearch = data.page_search ?? undefined
      setMessages((prev) => [
        ...prev,
        { id: newId(), role: 'assistant', content: data.reply, products: data.products, pageSearch },
      ])
      // Browsing questions update the page: show every match as product cards.
      if (pageSearch) navigate(searchHref(pageSearch))
    } catch (err) {
      if (sessionOwner.current !== owner) return
      setMessages((prev) => [
        ...prev,
        {
          id: newId(),
          role: 'assistant',
          notice: true,
          content:
            (err as Error).message ||
            "Our shopping assistant isn't available right now. You can still browse every product, price and size on the Products page.",
        },
      ])
    } finally {
      setIsSending(false)
    }
  }

  async function clearChat() {
    if (userId) {
      const res = await fetch('/api/chat/history', { method: 'DELETE' })
      if (!res.ok) return
    }
    setMessages([])
    setFocusProduct(null)
  }

  const value: ChatState = {
    messages,
    isOpen,
    isSending,
    focusProduct,
    open: () => setIsOpen(true),
    close: () => setIsOpen(false),
    askAbout: (product) => {
      setFocusProduct(product)
      setIsOpen(true)
    },
    clearFocusProduct: () => setFocusProduct(null),
    send,
    savedToAccount: userId !== null,
    clearChat,
  }

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>
}
