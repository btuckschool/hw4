import { NavLink, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import { useChat } from '../chat/useChat'
import Crest from './Crest'
import DanAvatar from './DanAvatar'

const links = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Products' },
  { to: '/about', label: 'About Us' },
]

export default function NavBar() {
  const { user, ready, logout } = useAuth()
  const chat = useChat()
  const { pathname } = useLocation()
  const navClass = ({ isActive }: { isActive: boolean }) => (isActive ? 'nav-link active' : 'nav-link')

  return (
    <header className="site-header">
      <div className="utility-bar">
        <div className="container utility-inner">
          <span className="motto">Lux et Veritas</span>
          <button className="utility-link" onClick={chat.open}>
            <DanAvatar size={20} />
            <span>
              Ask Handsome Dan<span className="utility-long"> about sizes and stock</span>
            </span>
          </button>
        </div>
      </div>
      <nav className="nav container" aria-label="Main">
        <NavLink to="/" className="brand" aria-label="Campus Customs home">
          <Crest size={34} className="brand-crest" onDark />
          <span className="brand-text">
            <span className="brand-name">Campus Customs</span>
            <span className="brand-tag">Yale Apparel</span>
          </span>
        </NavLink>
        <ul className="nav-links">
          {links.map((l) => (
            <li key={l.to}>
              <NavLink to={l.to} end={l.end} className={navClass}>
                {l.label}
              </NavLink>
            </li>
          ))}
        </ul>
        <ul className="nav-account">
          {!ready ? null : user ? (
            <>
              <li className="nav-greeting">Hi, {user.first_name}</li>
              <li>
                <button className="btn btn-light btn-small" onClick={() => void logout()}>
                  Log Out
                </button>
              </li>
            </>
          ) : (
            <>
              <li>
                <NavLink to="/login" state={{ from: pathname }} className={navClass}>
                  Log In
                </NavLink>
              </li>
              <li>
                <NavLink to="/create-account" state={{ from: pathname }} className="btn btn-light btn-small">
                  Create Account
                </NavLink>
              </li>
            </>
          )}
        </ul>
      </nav>
    </header>
  )
}
