import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { api } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import { useToast } from '../../components/Toast'

/** US37 — Bouton « Contacter » à placer sur la page d'une annonce :
 *    <ContactButton listingId={annonce.id} listingTitle={annonce.titre} ownerId={annonce.owner.id} />
 *  Au premier message la conversation est créée, puis on ouvre le fil. */
export default function ContactButton({ listingId, listingTitle, ownerId, label = 'Contacter le propriétaire' }) {
  const { user } = useAuth()
  const notify = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const [open, setOpen] = useState(false)
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  if (user && user.id === ownerId) return null
  if (!user) return <Link className="btn" to="/connexion" state={{ from: location.pathname }}>{label}</Link>

  async function onSubmit(e) {
    e.preventDefault()
    setBusy(true); setError('')
    try {
      const { conversation } = await api('/messaging/conversations/', {
        method: 'POST', body: { recipient: ownerId, listing_id: listingId, listing_title: listingTitle, body: text },
      })
      notify('Message envoyé.')
      navigate(`/messages/${conversation.id}`)
    } catch (err) { setError(err.fields.body?.[0] || err.fields.recipient?.[0] || err.message) } finally { setBusy(false) }
  }

  if (!open) return <button className="btn" onClick={() => setOpen(true)}>{label}</button>
  return (
    <form className="card contact-box" onSubmit={onSubmit}>
      <label htmlFor="contact-body">Votre message à propos de « {listingTitle} »</label>
      {error && <div className="alert">{error}</div>}
      <textarea id="contact-body" className="input" rows={4} maxLength={2000} value={text} autoFocus required
        placeholder="Bonjour, cet objet est-il disponible du … au … ?" onChange={(e) => setText(e.target.value)} />
      <div className="row between" style={{ marginTop: 12 }}>
        <button type="button" className="btn ghost" onClick={() => setOpen(false)}>Annuler</button>
        <button className="btn" disabled={busy || !text.trim()}>{busy ? 'Envoi…' : 'Envoyer'}</button>
      </div>
    </form>
  )
}