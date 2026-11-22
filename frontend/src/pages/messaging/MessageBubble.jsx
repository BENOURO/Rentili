import { useState } from 'react'

const hhmm = (iso) => new Date(iso).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })

/** Une bulle du fil de discussion. Ses propres messages peuvent être modifiés (US39) ou supprimés (US40). */
export default function MessageBubble({ message, mine, onEdit, onDelete }) {
  const [editing, setEditing] = useState(false)
  const [text, setText] = useState(message.body)
  const [busy, setBusy] = useState(false)

  async function save() {
    const next = text.trim()
    if (!next || busy) return
    if (next === message.body) { setEditing(false); return }
    setBusy(true)
    const ok = await onEdit(message.id, next)
    setBusy(false)
    if (ok) setEditing(false)
  }

  return (
    <div className={`bubble-row ${mine ? 'mine' : ''}`}>
      {editing ? (
        <div className="edit-box">
          <textarea className="input" rows={3} value={text} maxLength={2000} autoFocus onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Escape') setEditing(false) }} />
          <div className="row">
            <button className="btn ghost sm" onClick={() => { setText(message.body); setEditing(false) }}>Annuler</button>
            <button className="btn sm" onClick={save} disabled={busy || !text.trim()}>Enregistrer</button>
          </div>
        </div>
      ) : (
        <div className={`bubble ${message.is_deleted ? 'deleted' : ''}`}>{message.is_deleted ? 'Message supprimé' : message.body}</div>
      )}
      <div className="bubble-meta">
        <span>{hhmm(message.created_at)}</span>
        {message.edited_at && !message.is_deleted && <span>modifié</span>}
        {mine && !message.is_deleted && (
          <span className={`ticks ${message.read_at ? 'read' : ''}`} title={message.read_at ? 'Lu' : 'Envoyé'}>{message.read_at ? '✓✓' : '✓'}</span>
        )}
        {mine && !message.is_deleted && !editing && (
          <span className="bubble-actions">
            <button className="link-btn" onClick={() => { setText(message.body); setEditing(true) }}>Modifier</button>
            <button className="link-btn" onClick={() => onDelete(message.id)}>Supprimer</button>
          </span>
        )}
      </div>
    </div>
  )
}