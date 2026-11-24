import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import Avatar from './Avatar'
import { useToast } from './Toast'
import { useMessaging } from '../messaging/MessagingContext'

function Logo() {
  return (
    <Link to="/" className="logo">
      <span className="logo-mark">
        <svg viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="8" cy="15" r="4" /><path d="M10.8 12.2 20 3M17 6l3 3M14.5 8.5l2 2" />
        </svg>
      </span>
      <span className="logo-text">rentili</span>
    </Link>
  )
}

function UserMenu() {
  const { user, logout } = useAuth()
  const notify = useToast()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const ref = useRef(null)
  useEffect(() => {
    const close = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('click', close)
    return () => document.removeEventListener('click', close)
  }, [])

  async function onLogout() {
    navigate('/')  // quitter d'abord la page protégée, sinon elle redirigerait vers la connexion
    await logout()
    notify('Vous êtes déconnecté.')
  }

  return (
    <div className="menu" ref={ref}>
      <button className="menu-trigger" onClick={() => setOpen((o) => !o)} aria-label="Menu du compte"><Avatar user={user} /></button>
      {open && (
        <div className="menu-panel" onClick={() => setOpen(false)}>
          <div className="menu-head"><b>{user.first_name} {user.last_name}</b><div className="muted small">{user.email}</div></div>
          <hr />
          <Link to="/profil">Mon profil</Link>
          <Link to="/reservations">Mes réservations</Link>
          <Link to="/annonces?mine=true">Mes annonces</Link>
          <Link to="/messages">Messages</Link>
          <Link to="/avis">Mes avis</Link>
          <Link to="/profil/modifier">Modifier mon profil</Link>
          {user.is_staff && <a href="http://127.0.0.1:8000/admin/">Administration</a>}
          <hr />
          <button onClick={onLogout}>Se déconnecter</button>
        </div>
      )}
    </div>
  )
}

export default function Layout() {
  const { user } = useAuth()
  const { unread } = useMessaging()
  return (
    <>
      <nav className="nav">
        <div className="wrap">
          <Logo />
          <div className="nav-links">
            <NavLink to="/annonces">Objets</NavLink>
            {user && <NavLink to="/reservations">Réservations</NavLink>}
            <NavLink to="/membres">Membres</NavLink>
            {user && <NavLink to="/avis">Avis</NavLink>}
            {user && <NavLink to="/messages">Messages{unread > 0 && <span className="badge">{unread}</span>}</NavLink>}
            {user ? (
              <><NavLink to="/profil" className="hide-sm">Mon profil</NavLink><UserMenu /></>
            ) : (
              <><NavLink to="/connexion">Connexion</NavLink><Link to="/inscription" className="btn sm">S'inscrire</Link></>
            )}
          </div>
        </div>
      </nav>
      <main><Outlet /></main>
      <footer className="foot">
        <div className="wrap row between">
          <span>© 2026 RENTILI — Rent Everything, Everywhere, Anytime</span>
          <span>Module « Gestion des utilisateurs »</span>
        </div>
      </footer>
    </>
  )
}
