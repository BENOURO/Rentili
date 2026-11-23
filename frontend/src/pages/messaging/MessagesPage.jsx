import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import Avatar from '../../components/Avatar'
import { useMessaging } from '../../messaging/MessagingContext'
import Thread from './Thread'

const when = (iso) => {
  const d = new Date(iso)
  return d.toDateString() === new Date().toDateString()
    ? d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
    : d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })
}

function preview(c, meId) {
  const m = c.last_message
  if (!m) return ''
  if (m.is_deleted) return 'Message supprimé'
  return `${m.sender === meId ? 'Vous : ' : ''}${m.body}`
}

/** US38 — Boîte de réception (liste des conversations) + fil de discussion. */
export default function MessagesPage() {
  const { id } = useParams()
  const activeId = id ? Number(id) : null
  const { user } = useAuth()
  const { subscribe, connected } = useMessaging()
  const [conversations, setConversations] = useState(null)

  const load = useCallback(() => api('/messaging/conversations/').then((d) => setConversations(d.results)).catch(() => setConversations([])), [])
  useEffect(() => { load() }, [load])
  useEffect(() => subscribe(load), [subscribe, load])

  return (
    <div className="wrap page">
      <div className={`chat ${activeId ? 'has-active' : ''}`}>
        <aside className="chat-list">
          <div className="chat-list-head">
            <h2>Messages</h2>
            <span className={`live ${connected ? 'on' : ''}`}>{connected ? 'En direct' : 'Reconnexion…'}</span>
          </div>
          {conversations === null && <p className="muted small" style={{ padding: 18 }}>Chargement…</p>}
          {conversations?.length === 0 && (
            <div className="empty" style={{ border: 0 }}>
              <h3>Aucune conversation</h3>
              <p>Ouvrez une annonce et cliquez sur « Contacter » pour écrire à son propriétaire.</p>
            </div>
          )}
          {conversations?.map((c) => (
            <Link key={c.id} to={`/messages/${c.id}`} className={`chat-item ${c.id === activeId ? 'active' : ''} ${c.unread_count ? 'unread' : ''}`}>
              <Avatar user={c.other} size="md" />
              <div className="txt">
                <div className="top"><b>{c.other.display_name}</b><span className="muted small">{when(c.updated_at)}</span></div>
                <div className="listing">{c.listing_title || `Annonce n° ${c.listing_id}`}</div>
                <div className="preview">{preview(c, user.id)}</div>
              </div>
              {c.unread_count > 0 && <span className="badge">{c.unread_count}</span>}
            </Link>
          ))}
        </aside>
        <section className="chat-thread">
          {activeId ? <Thread key={activeId} conversationId={activeId} me={user} />
            : <div className="chat-empty"><div><h3>Vos échanges</h3><p>Choisissez une conversation pour afficher les messages.</p></div></div>}
        </section>
      </div>
    </div>
  )
}