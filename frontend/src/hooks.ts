import { useEffect, useState } from 'react'
import { fetchProducts, type ProductSummary } from './api'

// Products are fetched once per visit and shared by every page that needs them.
let cache: Promise<ProductSummary[]> | null = null

export function useProducts() {
  const [products, setProducts] = useState<ProductSummary[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    cache ??= fetchProducts()
    let active = true
    cache.then(
      (data) => active && setProducts(data),
      (err: Error) => {
        cache = null
        if (active) setError(err.message)
      },
    )
    return () => {
      active = false
    }
  }, [])

  return { products, error }
}
