// Types mirror backend/models.py.

export interface SizeStock {
  size: string
  quantity: number
}

export interface ProductSummary {
  product_id: string
  name: string
  garment_type: string
  description: string
  colors: string[]
  price: number
  image_url: string
  in_stock: boolean
}

export interface ProductDetail extends ProductSummary {
  search_tags: string[]
  sizes: SizeStock[]
  total_stock: number
}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`Request failed (${res.status})`)
  return res.json() as Promise<T>
}

export const fetchProducts = () => getJson<ProductSummary[]>('/api/products')

export const fetchProduct = (id: string) =>
  getJson<ProductDetail>(`/api/products/${encodeURIComponent(id)}`)

export const formatPrice = (price: number) =>
  price.toLocaleString('en-US', { style: 'currency', currency: 'USD' })

// ---------- Search (chat results shown on the Products page) ----------

export interface ProductFilters {
  keywords?: string | null
  category?: string | null
  color?: string | null
  size_in_stock?: string | null
  min_price?: number | null
  max_price?: number | null
}

export interface PageSearchResult {
  title: string
  filters: ProductFilters
  total: number
}

const FILTER_KEYS = ['keywords', 'category', 'color', 'size_in_stock', 'min_price', 'max_price'] as const

// The Products page URL for a search, e.g. /products?category=t-shirt&title=T-shirts.
// Keeping the search in the URL means refresh, back and forward all work.
export function searchHref(search: PageSearchResult): string {
  const params = new URLSearchParams()
  for (const key of FILTER_KEYS) {
    const value = search.filters[key]
    if (value !== null && value !== undefined && value !== '') params.set(key, String(value))
  }
  params.set('title', search.title)
  return `/products?${params}`
}

export function filtersFromParams(params: URLSearchParams): URLSearchParams | null {
  const filters = new URLSearchParams()
  for (const key of FILTER_KEYS) {
    const value = params.get(key)
    if (value) filters.set(key, value)
  }
  return filters.size > 0 ? filters : null
}

export const fetchSearch = (filters: URLSearchParams) =>
  getJson<{ total: number; products: ProductSummary[] }>(`/api/search?${filters}`)
