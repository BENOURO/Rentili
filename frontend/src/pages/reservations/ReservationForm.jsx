import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { api } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import Field from '../../components/Field'
import { useToast } from '../../components/Toast'
import { aujourdhui, dt, nbJours } from './format'

/** US21 — Demander la réservation d'un objet pour une période. Le prix est affiché avant l'envoi. */
export default function ReservationForm({ annonce }) {
  const { user } = useAuth()
  const notify = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({ date_debut: '', date_fin: '', message: '' })
  const [errors, setErrors] = useState({})
  const [busy, setBusy] = useState(false)
  const set = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  if (!user) {
    return (
      <div className="card">
        <h3>Réserver cet objet</h3>
        <p className="muted small">Connectez-vous pour envoyer une demande de réservation.</p>
        <Link className="btn block" to="/connexion" state={{ from: location.pathname }}>Se connecter</Link>
      </div>
    )
  }
  if (user.id === annonce.proprietaire.id) {
    return <div className="card"><h3>C'est votre annonce</h3><p className="muted small" style={{ margin: 0 }}>Les demandes reçues sont dans <Link to="/reservations?vue=recues">Mes réservations</Link>.</p></div>
  }

  const jours = nbJours(form.date_debut, form.date_fin)

  async function onSubmit(e) {
    e.preventDefault()
    setBusy(true); setErrors({})
    try {
      await api('/reservations/', { method: 'POST', body: { annonce_id: annonce.id, ...form } })
      notify('Demande envoyée au propriétaire.')
      navigate('/reservations')
    } catch (err) {
      setErrors(Object.keys(err.fields).length ? err.fields : { non_field_errors: [err.message] })
    } finally { setBusy(false) }
  }

  return (
    <form className="card" onSubmit={onSubmit} noValidate>
      <h3>Réserver cet objet</h3>
      {errors.non_field_errors && <div className="alert">{errors.non_field_errors.join(' ')}</div>}
      {errors.annonce_id && <div className="alert">{errors.annonce_id.join(' ')}</div>}
      {errors.detail && <div className="alert">{errors.detail}</div>}
      <div className="grid-2">
        <Field label="Du" name="date_debut" type="date" min={aujourdhui()} value={form.date_debut} onChange={set} errors={errors} required />
        <Field label="Au" name="date_fin" type="date" min={form.date_debut || aujourdhui()} value={form.date_fin} onChange={set} errors={errors} required />
      </div>
      <Field label="Message au propriétaire" name="message" as="textarea" rows={3} maxLength={1000} value={form.message} onChange={set} errors={errors}
        placeholder="À quoi va servir l'objet, heure de retrait souhaitée…" />
      {jours > 0 && (
        <div className="recap">
          <div className="row"><span>{dt(annonce.prix_jour)} × {jours} jour{jours > 1 ? 's' : ''}</span><span>{dt(annonce.prix_jour * jours)}</span></div>
          <div className="row muted"><span>Caution (rendue au retour)</span><span>{dt(annonce.caution)}</span></div>
          <div className="row total"><span>Total de la location</span><span>{dt(annonce.prix_jour * jours)}</span></div>
        </div>
      )}
      <button className="btn block" disabled={busy || !form.date_debut || !form.date_fin}>{busy ? 'Envoi…' : 'Envoyer la demande'}</button>
      <p className="muted small" style={{ margin: '10px 0 0' }}>Rien n'est payé maintenant : le propriétaire doit d'abord accepter.</p>
    </form>
  )
}
