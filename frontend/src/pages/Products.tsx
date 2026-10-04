import { useEffect, useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { fetchSearch, filtersFromParams, type ProductSummary } from '../api'
import ProductCard from '../components/ProductCard'
import { useProducts } from '../hooks'

const CATEGORIES = [
  ['hoodie', 'Hoodies'],
  ['crewneck', 'Crewnecks'],
  ['t-shirt', 'T-shirts'],
  ['quarter-zip', 'Quarter-zips'],
  ['jacket', 'Jackets'],
  ['long-sleeve shirt', 'Long-sleeve shirts'],
  ['mockneck', 'Mocknecks'],
]

// "Blue" includes every blue; navy and navy blue are the same (see the harness's Decisions).
const COLORS = [
  ['navy', 'Navy'],
  ['blue', 'Blue (all shades)'],
  ['royal blue', 'Royal blue'],
  ['light blue', 'Light blue'],
  ['gray', 'Gray'],
  ['white', 'White'],
  ['black', 'Black'],
  ['red', 'Red'],
  ['green', 'Green'],
  ['yellow', 'Yellow'],
]

const SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL']

const SORTS = [
  ['featured', 'Featured'],
  ['price-asc', 'Price: low to high'],
  ['price-desc', 'Price: high to low'],
  ['name', 'Name: A to Z'],
]

function sortProducts(products: ProductSummary[], sort: string): ProductSummary[] {
  const sorted = [...products]
  if (sort === 'price-asc') sorted.sort((a, b) => a.price - b.price || a.name.localeCompare(b.name))
  if (sort === 'price-desc') sorted.sort((a, b) => b.price - a.price || a.name.localeCompare(b.name))
  if (sort === 'name') sorted.sort((a, b) => a.name.localeCompare(b.name))
  return sorted
}

// Shows every product, or only those matching the filters in the URL. Filters come from the
// controls on this page or from a chat search; both use the same search as the assistant.
export default function Products() {
  const [params, setParams] = useSearchParams()
  const filters = filtersFromParams(params)
  const query = filters?.toString() ?? ''
  const chatTitle = params.get('title')
  const sort = params.get('sort') ?? 'featured'

  const all = useProducts()
  // Results are tagged with the query they belong to, so stale results never show.
  const [result, setResult] = useState<{ query: string; products?: ProductSummary[]; error?: string } | null>(
    null,
  )

  useEffect(() => {
    if (!query) return
    let active = true
    fetchSearch(new URLSearchParams(query)).then(
      (data) => active && setResult({ query, products: data.products }),
      (err: Error) => active && setResult({ query, error: err.message }),
    )
    return () => {
      active = false
    }
  }, [query])

  const current = query && result?.query === query ? result : null
  const found = query ? current?.products : all.products
  const products = found ? sortProducts(found, sort) : undefined
  const error = query ? current?.error : all.error

  // Changing a filter by hand means it's no longer the chat's search, so its title goes.
  function setParam(key: string, value: string) {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    if (key !== 'sort') next.delete('title')
    setParams(next)
  }

  function submitKeywords(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setParam('keywords', String(new FormData(e.currentTarget).get('keywords') ?? '').trim())
  }

  const clearHref = sort !== 'featured' ? `/products?sort=${sort}` : '/products'

  return (
    <div className="container page">
      <header className="page-header">
        <div>
          {chatTitle && query && <p className="eyebrow">From your chat</p>}
          <h1>{chatTitle && query ? chatTitle : query ? 'Products' : 'All products'}</h1>
        </div>
        <div className="page-header-meta">
          {products && <p>{products.length === 1 ? '1 style' : `${products.length} styles`}</p>}
          {query && (
            <Link to={clearHref} className="text-link">
              {chatTitle ? 'Show all products' : 'Clear filters'}
            </Link>
          )}
        </div>
      </header>

      <div className="filter-bar" role="search" aria-label="Filter products">
        <form className="filter-search" onSubmit={submitKeywords} key={params.get('keywords') ?? ''}>
          <input
            name="keywords"
            type="search"
            placeholder="Search: Saybrook, bulldog, hockey…"
            defaultValue={params.get('keywords') ?? ''}
            aria-label="Search products"
          />
          <button type="submit" className="btn btn-primary btn-small">
            Search
          </button>
        </form>
        <label>
          Category
          <select value={params.get('category') ?? ''} onChange={(e) => setParam('category', e.target.value)}>
            <option value="">All</option>
            {CATEGORIES.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Color
          <select value={params.get('color') ?? ''} onChange={(e) => setParam('color', e.target.value)}>
            <option value="">Any</option>
            {COLORS.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label>
          In stock in
          <select
            value={params.get('size_in_stock') ?? ''}
            onChange={(e) => setParam('size_in_stock', e.target.value)}
          >
            <option value="">Any size</option>
            {SIZES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label>
          Sort
          <select value={sort} onChange={(e) => setParam('sort', e.target.value === 'featured' ? '' : e.target.value)}>
            {SORTS.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {error && <p className="status-message">We couldn't load products right now.</p>}
      {!products && !error && <p className="status-message">Loading products…</p>}
      {products && products.length === 0 && (
        <p className="status-message">
          No products match these filters. <Link to={clearHref}>Clear filters</Link>
        </p>
      )}

      {products && products.length > 0 && (
        <div className="product-grid">
          {products.map((p) => (
            <ProductCard key={p.product_id} product={p} />
          ))}
        </div>
      )}
    </div>
  )
}
