import { Link } from 'react-router-dom'
import Crest from '../components/Crest'
import DanAvatar from '../components/DanAvatar'
import { useProducts } from '../hooks'

// Every list below comes from what's actually in the catalogue.
const collections = [
  {
    title: 'Residential colleges',
    body: 'Benjamin Franklin, Berkeley, Branford, Davenport, Grace Hopper, Jonathan Edwards, Morse, Pierson, Saybrook, Timothy Dwight and Trumbull.',
  },
  {
    title: 'Graduate & professional schools',
    body: 'Architecture, Art, Divinity, Engineering, the Forest School, Law, Management, Medicine, Music, Nursing and Public Health.',
  },
  {
    title: 'Varsity sports',
    body: 'Baseball, basketball, diving, fencing, field hockey, football, golf, hockey, lacrosse, sailing, soccer, squash, swimming, tennis, track & field and volleyball.',
  },
  {
    title: 'The whole family',
    body: 'Styles made for Yale moms, dads, grandmas, grandpas, aunts, uncles, brothers and cousins.',
  },
]

export default function About() {
  const { products } = useProducts()

  return (
    <div className="page">
      <section className="about-hero">
        <div className="container narrow about-hero-inner">
          <Crest size={72} className="about-crest" />
          <p className="eyebrow">About us</p>
          <h1>Yale pride, made to wear every day.</h1>
          <p className="lead">
            Campus Customs is a shop for Yale apparel. We put together crewnecks, hoodies, T-shirts,
            quarter-zips and jackets for everyone with a connection to Yale, from first-years on Old
            Campus to alumni and the relatives who show up for every game.
          </p>
        </div>
      </section>

      <section className="container narrow about-section">
        <h2>What we carry</h2>
        <p>
          {products ? `${products.length} styles` : 'Our styles'} come in sizes XS through XXL, from
          brands including Champion, Under Armour, Brooks Brothers, District and Hype and Vice.
        </p>
        <div className="about-grid">
          {collections.map((c) => (
            <div key={c.title} className="about-card">
              <h3>{c.title}</h3>
              <p>{c.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="container narrow about-section">
        <h2 className="about-dan-heading">
          <DanAvatar size={48} /> Meet Handsome Dan
        </h2>
        <p>
          Our bulldog shopping guide waits in the corner of every page. Ask him to find something,
          compare styles or check what's in stock in your size. He answers from the same live catalogue
          and inventory you see on the site, and if you're logged in, he'll remember your last chat.
        </p>
        <Link to="/products" className="btn btn-primary">
          Browse products
        </Link>
      </section>
    </div>
  )
}
