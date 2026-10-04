import { useEffect, useRef } from 'react'
import { Link, Route, Routes, useLocation } from 'react-router-dom'
import { useChat } from './chat/useChat'
import ChatWidget from './chat/ChatWidget'
import Footer from './components/Footer'
import NavBar from './components/NavBar'
import About from './pages/About'
import { CreateAccount, Login } from './pages/AccountForms'
import Home from './pages/Home'
import ProductPage from './pages/ProductPage'
import Products from './pages/Products'

function NotFound() {
  return (
    <div className="container page">
      <h1>Page not found</h1>
      <Link to="/" className="text-link">
        Back to home
      </Link>
    </div>
  )
}

export default function App() {
  const { isOpen } = useChat()
  const { pathname, search } = useLocation()

  // On phones the page scrolls inside .page-scroll rather than the window.
  const scrollRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    window.scrollTo(0, 0)
    scrollRef.current?.scrollTo(0, 0)
  }, [pathname, search])

  // The chat never covers the page: on desktop the page makes room beside an open
  // panel; on phones the chat gets its own strip below the scrolling page.
  return (
    <div className={isOpen ? 'app chat-open' : 'app'}>
      <div className="page-scroll" ref={scrollRef}>
        <NavBar />
        <main className="site-main">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/products" element={<Products />} />
            <Route path="/products/:productId" element={<ProductPage />} />
            <Route path="/about" element={<About />} />
            <Route path="/login" element={<Login />} />
            <Route path="/create-account" element={<CreateAccount />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
        <Footer />
      </div>
      <ChatWidget />
    </div>
  )
}
