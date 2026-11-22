import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import Avatar from '../../components/Avatar'
import { monthYear } from './format'

/** US05 — Profil public : prénom + initiale, ville, ancienneté, présentation. Jamais l'email ni le téléphone. */
export default function PublicProfilePage() {
  const { id } = useParams()
  const { user } = useAuth()
  const [member, setMember] = useState(null)
  const [missing, setMissing] = useState(false)

  useEffect(() => {
    api(`/users/${id}/`).then(setMember).catch(() => setMissing(true))
  }, [id])

  if (missing) return <div className="wrap page"><div className="empty"><h3>Ce profil n'existe pas ou a été supprimé.</h3><Link className="btn" to="/membres">Voir les membres</Link></div></div>
  if (!member) return <div className="wrap page muted">Chargement…</div>
  const isMe = user && user.id === member.id

  return (
    <div className="wrap page">
      {isMe && <div className="alert info">Voici comment les autres membres voient votre profil.</div>}
      <div className="profile-head">
        <Avatar user={member} size="lg" />
        <div className="grow">
          <h1 style={{ margin: 0 }}>{member.display_name}</h1>
          <p className="muted" style={{ margin: '4px 0 0' }}>{member.city && `${member.city} · `}Membre depuis {monthYear(member.date_joined)}</p>
        </div>
      </div>
      <div className="card mb">
        <h3>Présentation</h3>
        {member.bio ? <p className="pre" style={{ margin: 0 }}>{member.bio}</p> : <p className="muted" style={{ margin: 0 }}>{member.first_name} n'a pas encore écrit de présentation.</p>}
      </div>
      <p className="small muted">Les annonces et les avis de ce membre s'afficheront ici une fois les modules Annonces et Avis intégrés.</p>
    </div>
  )
}
