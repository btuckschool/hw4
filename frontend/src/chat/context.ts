import { createContext } from 'react'
import type { PageSearchResult, ProductSummary } from '../api'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  products?: ProductSummary[]
  // A search whose full results were shown on the Products page.
  pageSearch?: PageSearchResult
  // Marks app notices (e.g. the assistant being offline) so they aren't sent back as history.
  notice?: boolean
}

export interface ChatState {
  messages: ChatMessage[]
  isOpen: boolean
  isSending: boolean
  focusProduct: ProductSummary | null
  open: () => void
  close: () => void
  askAbout: (product: ProductSummary) => void
  clearFocusProduct: () => void
  send: (text: string) => Promise<void>
  // Logged-in shoppers' chats are saved to their account; guests' last only for this tab.
  savedToAccount: boolean
  clearChat: () => Promise<void>
}

export const ChatContext = createContext<ChatState | null>(null)
