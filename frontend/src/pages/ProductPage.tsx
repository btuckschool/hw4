import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct, formatPrice, type ProductDetail } from '../api'
import { useChat } from '../chat/useChat'

export default function ProductPage() {
  const { productId = '' } = useParams()
  const { askAbout } = useChat()
  // Results are tagged with the ID they belong to, so a stale product never shows after navigating.
  const [result, setResult] = useState<{ id: string; product?: ProductDetail; error?: string } | null>(null)

  useEffect(() => {
    let active = true
    fetchProduct(productId).then(
      (product) => active && setResult({ id: productId, product }),
      (err: Error) => active && setResult({ id: productId, error: err.message }),
    )
    return () => {
      active = false
    }
  }, [productId])

  const current = result?.id === productId ? result : null
  const product = current?.product
  const error = current?.error

  if (error) {
    return (
      <div className="container page">
        <p className="status-message">We couldn't find that product.</p>
        <Link to="/products" className="text-link">
          ← Back to all products
        </Link>
      </div>
    )
  }

  if (!product) return <p className="container page status-message">Loading…</p>

  return (
    <div className="container page">
      <Link to="/products" className="text-link back-link">
        ← All products
      </Link>
      <div className="product-detail">
        <div className="product-detail-image">
          <img src={product.image_url} alt={product.name} />
        </div>

        <div className="product-detail-info">
          <p className="eyebrow">{product.garment_type}</p>
          <h1>{product.name}</h1>
          <p className="product-detail-price">{formatPrice(product.price)}</p>
          <p className="product-detail-desc">{product.description}</p>

          <p className="product-detail-colors">
            <span className="label">Design colors:</span> {product.colors.join(', ')}
          </p>

          <h2 className="label">Sizes and stock</h2>
          {product.in_stock ? (
            <ul className="size-list">
              {product.sizes.map((s) => (
                <li key={s.size} className={s.quantity > 0 ? 'size in' : 'size out'}>
                  <span className="size-name">{s.size}</span>
                  <span className="size-qty">{s.quantity > 0 ? `${s.quantity} in stock` : 'Out of stock'}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="out-of-stock">This item is out of stock in every size.</p>
          )}

          <button className="btn btn-primary" onClick={() => askAbout(product)}>
            Ask about this
          </button>
        </div>
      </div>
    </div>
  )
}
