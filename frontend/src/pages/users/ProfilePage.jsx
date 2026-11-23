import { Link } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import Avatar from '../../components/Avatar'
import { monthYear } from './format'

/** US03 — Consulter son profil. */
export default function ProfilePage() {
  const { user } = useAuth()
  return (
    <div className="wrap page">
      <div className="profile-head">
        <Avatar user={user} size="lg" />
        <div className="grow">
          <h1 style={{ margin: 0 }}>{user.first_name} {user.last_name}</h1>
          <p className="muted" style={{ margin: '4px 0 0' }}>{user.city && `${user.city} · `}Membre depuis {monthYear(user.date_joined)}</p>
        </div>
        <Link className="btn ghost" to="/profil/modifier">Modifier mon profil</Link>
      </div>

      <div className="card mb">
        <h3>Présentation</h3>
        {user.bio ? <p className="pre" style={{ margin: 0 }}>{user.bio}</p> : <p className="muted" style={{ margin: 0 }}>Vous n'avez pas encore écrit de présentation.</p>}
      </div>

      <div className="card mb">
        <h3>Mes informations privées</h3>
        <div className="grid-2 small">
          <p><span className="muted">Email</span><br />{user.email}</p>
          <p><span className="muted">Téléphone</span><br />{user.phone || '—'}</p>
        </div>
        <p className="small muted" style={{ margin: 0 }}>Ces informations ne sont jamais affichées sur votre profil public.</p>
      </div>

      <div className="row small" style={{ marginTop: 30, gap: 18 }}>
        <Link className="muted" to={`/membres/${user.id}`}>Voir mon profil public</Link>
        <Link className="muted" to="/profil/supprimer">Supprimer mon compte</Link>
      </div>
    </div>
  )
}
