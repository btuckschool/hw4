import { Link } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import Crest from './Crest'

export default function Footer() {
  const { user } = useAuth()

  return (
    <footer className="site-footer">
      <div className="container footer-inner">
        <div className="footer-id">
          <Crest size={44} className="footer-crest" onDark />
          <div>
            <p className="footer-brand">Campus Customs</p>
            <p className="footer-tagline">Yale apparel for students, alumni and families.</p>
            <p className="footer-motto">Lux et Veritas</p>
          </div>
        </div>
        <ul className="footer-links">
          <li>
            <Link to="/products">Products</Link>
          </li>
          <li>
            <Link to="/about">About Us</Link>
          </li>
          {!user && (
            <>
              <li>
                <Link to="/login">Log In</Link>
              </li>
              <li>
                <Link to="/create-account">Create Account</Link>
              </li>
            </>
          )}
        </ul>
      </div>
    </footer>
  )
}
