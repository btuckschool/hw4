import { Link } from 'react-router-dom'
import Crest from '../components/Crest'
import ProductCard from '../components/ProductCard'
import { searchHref } from '../api'
import { useProducts } from '../hooks'

// Featured rows are hand-picked catalogue IDs, so every item shown is real stock.
const sections = [
  {
    title: 'Layers for cooler days',
    blurb: 'Fleece, quarter-zips and jackets to wear from class to the Commons.',
    ids: [
      'benjamin-franklin-fleece-jacket',
      'school-of-art-1-4-zip',
      'champion-full-zip-hood',
      'brooks-brothers-bomber-jacket-yale',
    ],
  },
  {
    title: 'Cheer on the Bulldogs',
    blurb: 'Gear for game day, whatever the sport.',
    ids: [
      'yale-sports-hoodie-hockey',
      'football-left-chest-t-shirt',
      'tri-blend-sports-basketball-t-shirt',
      '2025-yale-vs-harvard-t-shirt',
    ],
  },
  {
    title: 'Pride runs in the family',
    blurb: 'Pieces made for the parents, grandparents and relatives in the stands.',
    ids: ['yale-mom-hoodie', 'yale-dad-crewneck', 'yale-grandpa-hoodie', 'yale-aunt-hoodie'],
  },
  {
    title: 'Rep your residential college',
    blurb: 'Crests and colors for the college you call home.',
    ids: [
      'davenport-college-crewneck',
      'pierson-logo-t-shirt',
      'morse-1-4-zip',
      'saybrook-sweater-fleece-jacket',
    ],
  },
]

// Residential colleges with products in the catalogue; each link opens that college's items.
const COLLEGES = [
  'Benjamin Franklin',
  'Berkeley',
  'Branford',
  'Davenport',
  'Grace Hopper',
  'Jonathan Edwards',
  'Morse',
  'Pierson',
  'Saybrook',
  'Timothy Dwight',
  'Trumbull',
]

export default function Home() {
  const { products, error } = useProducts()
  const byId = new Map(products?.map((p) => [p.product_id, p]))

  return (
    <>
      <section className="hero">
        <Crest size={360} className="hero-watermark" />
        <div className="container hero-inner">
          <div className="hero-copy">
            <p className="eyebrow">Yale apparel · Bulldogs, colleges and schools</p>
            <h1>Wear your Bulldog spirit.</h1>
            <p className="hero-lead">
              Crewnecks, hoodies, tees and layers for students, alumni and the families who cheer them on.
            </p>
            <div className="hero-actions">
              <Link to="/products" className="btn btn-light">
                Shop all products
              </Link>
              <Link to="/about" className="btn btn-ghost">
                Our story
              </Link>
            </div>
          </div>
          <div className="hero-image">
            <img src="/images/basic-hoodie-big-yale.jpg" alt="Navy Yale pullover hoodie" />
          </div>
        </div>
      </section>

      <section className="college-strip" aria-labelledby="college-heading">
        <div className="container">
          <h2 id="college-heading">Shop by residential college</h2>
          <ul className="college-list">
            {COLLEGES.map((c) => (
              <li key={c}>
                <Link to={searchHref({ title: `${c} College`, filters: { keywords: c }, total: 0 })}>{c}</Link>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {error && <p className="container status-message">We couldn't load products right now.</p>}

      {sections.map((s) => {
        const items = s.ids.map((id) => byId.get(id)).filter((p) => p !== undefined)
        return (
          <section key={s.title} className="home-section container">
            <div className="section-heading">
              <div>
                <h2>{s.title}</h2>
                <p>{s.blurb}</p>
              </div>
              <Link to="/products" className="text-link">
                View all →
              </Link>
            </div>
            <div className="product-grid">
              {items.map((p) => (
                <ProductCard key={p.product_id} product={p} />
              ))}
            </div>
          </section>
        )
      })}
    </>
  )
}
