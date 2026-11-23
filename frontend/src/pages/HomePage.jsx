import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import MemberCard from './users/MemberCard'

export default function HomePage() {
  const { user } = useAuth()
  const [members, setMembers] = useState({ count: 0, results: [] })
  useEffect(() => { api('/users/').then(setMembers).catch(() => {}) }, [])

  return (
    <>
      <section className="hero">
        <div className="hero-deco" />
        <div className="wrap">
          <p className="eyebrow">Module « Gestion des utilisateurs »</p>
          <h1>Un compte pour <em>louer</em><br />et proposer des objets.</h1>
          <p className="lead">Inscription, connexion sécurisée, profil et profil public : la base de confiance de RENTILI,
            la plateforme tunisienne de location d'objets entre particuliers.</p>
          <div className="row">
            {user ? (
              <><Link className="btn" to="/profil">Voir mon profil</Link><Link className="btn ghost" to="/avis">Voir les avis</Link></>
            ) : (
              <><Link className="btn" to="/inscription">Créer un compte</Link><Link className="btn ghost" to="/connexion">Se connecter</Link></>
            )}
          </div>
          <div className="hero-stats">
            <div><b>{members.count}</b>membres</div><div><b>1</b>compte pour louer et proposer</div><div><b>0 DT</b>d'inscription</div>
          </div>
        </div>
      </section>
      <div className="wrap">
        <section className="section">
          <h2>Ce que couvre ce module</h2>
          <div className="steps">
            <div className="step"><b>US01–02</b><h3>Inscription et connexion</h3><p className="muted">Compte par email, mot de passe haché, connexion et déconnexion.</p></div>
            <div className="step"><b>US03–04</b><h3>Mon profil</h3><p className="muted">Consulter et modifier ses informations : nom, ville, téléphone, présentation, photo.</p></div>
            <div className="step"><b>US05–06</b><h3>Confiance et contrôle</h3><p className="muted">Profil public sans données privées, et suppression du compte avec anonymisation.</p></div>
          </div>
        </section>
        {members.results.length > 0 && (
          <section className="section" style={{ paddingBottom: 60 }}>
            <div className="row between"><h2>Nouveaux membres</h2><Link to="/membres" className="muted">Tout voir →</Link></div>
            <div className="member-grid">{members.results.slice(0, 6).map((m) => <MemberCard key={m.id} member={m} />)}</div>
          </section>
        )}
      </div>
    </>
  )
}
