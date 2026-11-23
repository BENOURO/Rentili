export default function Navbar() {
  return (
    <nav className="nav">
      <div className="wrap">
        <a className="logo" href="/" aria-label="Rentili accueil">
          <span className="logo-mark" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none">
              <path d="M4 20V8l8-4 8 4v12M8 20v-7h8v7M3 20h18" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </span>
          <span className="logo-text">Rentili</span>
        </a>
        <div className="nav-links">
          <a href="#avis">Avis</a>
          <a href="#ajouter">Ajouter un avis</a>
          <button className="avatar" type="button" aria-label="Profil utilisateur">AB</button>
        </div>
      </div>
    </nav>
  )
}
