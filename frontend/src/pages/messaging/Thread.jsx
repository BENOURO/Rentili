import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import Avatar from '../../components/Avatar'
import { useToast } from '../../components/Toast'
import { useMessaging } from '../../messaging/MessagingContext'
import MessageBubble from './MessageBubble'

const upsert = (list, m) => (!list ? list : list.some((x) => x.id === m.id) ? list.map((x) => (x.id === m.id ? m : x)) : [...list, m])
const dayLabel = (iso) => new Date(iso).toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })

/** US38 — Fil de discussion d'une conversation, mis à jour en temps réel. */
export default function Thread({ conversationId, me }) {
  const notify = useToast()
  const { subscribe } = useMessaging()
  const [conv, setConv] = useState(null)
  const [messages, setMessages] = useState(null)
  const [hasMore, setHasMore] = useState(false)
  const [missing, setMissing] = useState(false)
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const body = useRef(null)
  const skipScroll = useRef(false)
  const base = `/messaging/conversations/${conversationId}`

  const markRead = useCallback(() => api(`${base}/read/`, { method: 'POST' }).catch(() => {}), [base])

  useEffect(() => {
    Promise.all([api(`${base}/`), api(`${base}/messages/`)])
      .then(([c, m]) => { setConv(c); setMessages(m.results); setHasMore(m.has_more); markRead() })
      .catch(() => setMissing(true))
  }, [base, markRead])

  useEffect(() => subscribe((evt) => {
    if (evt.conversation !== conversationId) return
    if (evt.event === 'messages.read') {
      setMessages((l) => l && l.map((m) => (evt.message_ids.includes(m.id) ? { ...m, read_at: evt.read_at } : m)))
    } else if (evt.message) {
      setMessages((l) => upsert(l, evt.message))
      if (evt.event === 'message.created' && evt.message.sender !== me.id) markRead()
    }
  }), [subscribe, conversationId, me.id, markRead])

  useEffect(() => {
    if (skipScroll.current) { skipScroll.current = false; return }
    if (body.current) body.current.scrollTop = body.current.scrollHeight
  }, [messages?.length])

  async function loadOlder() {
    const el = body.current, height = el.scrollHeight
    const d = await api(`${base}/messages/?before=${messages[0].id}`)
    skipScroll.current = true
    setMessages((l) => [...d.results, ...l]); setHasMore(d.has_more)
    requestAnimationFrame(() => { el.scrollTop = el.scrollHeight - height })
  }

  async function send(e) {
    e?.preventDefault()
    const text = draft.trim()
    if (!text || busy) return
    setBusy(true)
    try {
      const m = await api(`${base}/messages/`, { method: 'POST', body: { body: text } })
      setMessages((l) => upsert(l, m)); setDraft('')
    } catch (err) { notify(err.fields.body?.[0] || err.message, 'error') } finally { setBusy(false) }
  }

    async function edit(id, text) {
    try {
      const m = await api(`/messaging/messages/${id}/`, { method: 'PATCH', body: { body: text } })
      setMessages((l) => upsert(l, m))
      return true
    } catch (err) {
      notify(err.fields.body?.[0] || err.message, 'error')
      return false
    }
  }

  async function remove(id) {
    if (!window.confirm('Supprimer ce message ? Son contenu sera retiré pour les deux participants.')) return
    try {
      await api(`/messaging/messages/${id}/`, { method: 'DELETE' })
      setMessages((l) => l.map((m) => (m.id === id ? { ...m, body: '', is_deleted: true } : m)))
    } catch (err) { notify(err.message, 'error') }
  }

  if (missing) return <div className="chat-empty"><div><h3>Conversation introuvable</h3><Link className="btn" to="/messages">Retour aux messages</Link></div></div>
  if (!conv || !messages) return <div className="chat-empty">Chargement…</div>

  return (
    <>
      <div className="thread-head">
        <Link className="back btn ghost sm" to="/messages" aria-label="Retour">←</Link>
        <Avatar user={conv.other} />
        <div className="grow" style={{ minWidth: 0 }}>
          <Link to={`/membres/${conv.other.id}`} style={{ textDecoration: 'none' }}><b>{conv.other.display_name}</b></Link>
          <div className="muted small">À propos de : {conv.listing_title || `annonce n° ${conv.listing_id}`}</div>
        </div>
      </div>
      <div className="thread-body" ref={body}>
        {hasMore && <button className="btn ghost sm older" onClick={loadOlder}>Messages précédents</button>}
        {messages.map((m, i) => {
          const day = new Date(m.created_at).toDateString()
          const sep = i === 0 || day !== new Date(messages.at(i - 1).created_at).toDateString()
          return (
            <div key={m.id} style={{ display: 'contents' }}>
              {sep && <span className="day-sep">{dayLabel(m.created_at)}</span>}
              <MessageBubble message={m} mine={m.sender === me.id} onEdit={edit} onDelete={remove} />
            </div>
          )
        })}
      </div>
      <form className="composer" onSubmit={send}>
        <textarea className="input" rows={1} value={draft} maxLength={2000} placeholder="Écrivez votre message…"
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) send(e) }} />
        <button className="btn" disabled={busy || !draft.trim()}>Envoyer</button>
      </form>
    </>
  )
}