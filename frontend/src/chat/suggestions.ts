// Starter questions for the chat, chosen for the page the shopper is on. Tapping one sends it,
// which helps shoppers who don't know what to ask and shows what the assistant can do.

const GENERAL = [
  'What kinds of t-shirts do you have?',
  'Show me navy hoodies under $70',
  'Anything with a bulldog on it?',
  'What crewnecks do you have in XL?',
]

const PRODUCT = ['What sizes are in stock?', 'Does this come in other colors?', 'Show me similar items']

const SEARCH = ['Which of these are in stock in M?', 'Which of these is the cheapest?', 'Show me these in gray']

export function suggestionsFor(
  pathname: string,
  search: string,
  hasFocusProduct: boolean,
): { questions: string[]; pageSpecific: boolean } {
  if (hasFocusProduct || /^\/products\/[^/]+$/.test(pathname)) return { questions: PRODUCT, pageSpecific: true }
  if (pathname === '/products' && new URLSearchParams(search).size > 0) {
    return { questions: SEARCH, pageSpecific: true }
  }
  return { questions: GENERAL, pageSpecific: false }
}
