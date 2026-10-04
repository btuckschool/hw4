import { Link } from 'react-router-dom'
import { formatPrice, type ProductSummary } from '../api'
import { useChat } from '../chat/useChat'

export default function ProductCard({ product }: { product: ProductSummary }) {
  const { askAbout } = useChat()
  const href = `/products/${product.product_id}`

  return (
    <article className="product-card">
      <Link to={href} className="product-card-link">
        <div className="product-card-image">
          <img src={product.image_url} alt={product.name} loading="lazy" />
          {!product.in_stock && <span className="badge-soldout">Sold out</span>}
        </div>
        <div className="product-card-body">
          <h3 className="product-card-name">{product.name}</h3>
          <p className="product-card-price">{formatPrice(product.price)}</p>
          <p className="product-card-desc">{product.description}</p>
        </div>
      </Link>
      <button className="btn btn-outline btn-small product-card-ask" onClick={() => askAbout(product)}>
        Ask about this
      </button>
    </article>
  )
}
