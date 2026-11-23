import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import Field from '../../components/Field'
import { useToast } from '../../components/Toast'
import { aujourdhui, dt, periode } from './format'
import StatutBadge from './StatutBadge'

/** Une réservation, vue par le locataire ou par le propriétaire, avec les actions permises par l'API :
 *  US22 accepter / refuser · US24 annuler · US25 modifier les dates · US26 terminer. */
export default function ReservationCard({ resa, onChange }) {
  const notify = useToast()
  const [mode, setMode] = useState(null) // null | 'refuser' | 'modifier' | 'annuler'
  const [motif, setMotif] = useState('')
  const [dates, setDates] = useState({ date_debut: resa.date_debut, date_fin: resa.date_fin })
  const [errors, setErrors] = useState({})
  const [busy, setBusy] = useState(false)
  const [avisStats, setAvisStats] = useState(null)
  const a = resa.actions
  const proprio = resa.role === 'proprietaire'

  useEffect(() => {
    if (resa.statut !== 'TERMINEE') return
    api('/avis/')
      .then((avis) => {
        const selected = Array.isArray(avis)
          ? avis.filter((item) => item.annonce_id === resa.annonce.id)
          : []
        const count = selected.length
        const average = count
          ? selected.reduce((total, item) => total + item.note, 0) / count
          : null
        setAvisStats({ count, average })
      })
      .catch(() => setAvisStats({ count: 0, average: null }))
  }, [resa.statut, resa.annonce.id])

  async function run(path, { body, method = 'POST', ok }) {
    setBusy(true); setErrors({})
    try {
      onChange(await api(`/reservations/${resa.id}/${path}`, { method, body }))
      setMode(null)
      notify(ok)
    } catch (err) {
      setErrors(Object.keys(err.fields).length ? err.fields : { detail: err.message })
    } finally { setBusy(false) }
  }

  const erreurGlobale = errors.detail || errors.non_field_errors?.join(' ')

  return (
    <article className="card resa">
      <div className="resa-head">
        <div>
          <h3><Link to={`/annonces/${resa.annonce.id}`}>{resa.annonce.titre}</Link></h3>
          <span className="muted small">
            {proprio ? <>Demandé par <Link to={`/membres/${resa.locataire.id}`}>{resa.locataire.display_name}</Link></>
              : <>Propriétaire : <Link to={`/membres/${resa.annonce.proprietaire.id}`}>{resa.annonce.proprietaire.display_name}</Link></>}
            {' · '}réservation n° {resa.id}
          </span>
        </div>
        <StatutBadge statut={resa.statut} />
      </div>

      <div className="resa-meta">
        <span>📅 {periode(resa.date_debut, resa.date_fin)} ({resa.nb_jours} j)</span>
        <span>💰 <b>{dt(resa.prix_total)}</b></span>
        <span>🔒 caution {dt(resa.caution)}</span>
      </div>

      {resa.message && <div className="resa-note">« {resa.message} »</div>}
      {resa.statut === 'REFUSEE' && resa.motif_refus && <div className="resa-note refus">Motif du refus : {resa.motif_refus}</div>}
      {resa.statut === 'TERMINEE' && !proprio && (
        <div className="resa-note">
          <div className="row" style={{ justifyContent: 'space-between' }}>
            <span>Location terminée.</span>
            {avisStats && (
              <span className="small" aria-label={`Note moyenne ${avisStats.average ?? 0} sur 5`}>
                <span style={{ color: '#e0a12a', letterSpacing: 1 }}>
                  {'★'.repeat(Math.round(avisStats.average || 0))}
                  {'☆'.repeat(5 - Math.round(avisStats.average || 0))}
                </span>
                {' '}
                <b>{avisStats.average ? avisStats.average.toFixed(1) : '0.0'}/5</b>
                {' · '}
                {avisStats.count} avis
              </span>
            )}
          </div>
          <div className="row" style={{ marginTop: 8 }}>
            <Link
              className="btn sm"
              to={`/avis?reservation=${resa.id}&annonce=${resa.annonce.id}`}
            >
              Donner mon avis
            </Link>
            <Link
              className="btn ghost sm"
              to={`/avis?annonce=${resa.annonce.id}`}
            >
              Voir les avis
            </Link>
          </div>
        </div>
      )}
      {erreurGlobale && <div className="alert" style={{ margin: 0 }}>{erreurGlobale}</div>}

      {mode === 'refuser' && (
        <form className="resa-form" onSubmit={(e) => { e.preventDefault(); run('refuser/', { body: { motif }, ok: 'Demande refusée.' }) }}>
          <Field label="Motif du refus (facultatif)" name="motif" value={motif} maxLength={300} onChange={(e) => setMotif(e.target.value)} errors={errors}
            placeholder="Objet indisponible, en réparation…" autoFocus />
          <div className="row"><button className="btn danger sm" disabled={busy}>Confirmer le refus</button><button type="button" className="btn ghost sm" onClick={() => setMode(null)}>Retour</button></div>
        </form>
      )}

      {mode === 'modifier' && (
        <form className="resa-form" onSubmit={(e) => { e.preventDefault(); run('', { method: 'PATCH', body: dates, ok: 'Dates modifiées, prix recalculé.' }) }}>
          <div className="grid-2">
            <Field label="Du" name="date_debut" type="date" min={aujourdhui()} value={dates.date_debut} errors={errors}
              onChange={(e) => setDates({ ...dates, date_debut: e.target.value })} required />
            <Field label="Au" name="date_fin" type="date" min={dates.date_debut} value={dates.date_fin} errors={errors}
              onChange={(e) => setDates({ ...dates, date_fin: e.target.value })} required />
          </div>
          <div className="row"><button className="btn sm" disabled={busy}>Enregistrer les dates</button><button type="button" className="btn ghost sm" onClick={() => setMode(null)}>Retour</button></div>
        </form>
      )}

      {mode === 'annuler' && (
        <div className="resa-form">
          <span>Annuler cette {resa.statut === 'ACCEPTEE' ? 'réservation' : 'demande'} ? {proprio ? 'Le locataire' : 'Le propriétaire'} verra qu'elle a été annulée.</span>
          <div className="row"><button className="btn danger sm" disabled={busy} onClick={() => run('annuler/', { ok: 'Réservation annulée.' })}>Oui, annuler</button><button className="btn ghost sm" onClick={() => setMode(null)}>Non</button></div>
        </div>
      )}

      {mode === null && (a.accepter || a.refuser || a.modifier || a.annuler || a.terminer) && (
        <div className="resa-actions">
          {a.accepter && <button className="btn sm" disabled={busy} onClick={() => run('accepter/', { ok: 'Demande acceptée.' })}>Accepter</button>}
          {a.refuser && <button className="btn danger sm" onClick={() => setMode('refuser')}>Refuser</button>}
          {a.terminer && <button className="btn sm" disabled={busy} onClick={() => run('terminer/', { ok: 'Location marquée comme terminée.' })}>Terminer la location</button>}
          {a.modifier && <button className="btn ghost sm" onClick={() => setMode('modifier')}>Modifier les dates</button>}
          {a.annuler && <button className="btn ghost sm" onClick={() => setMode('annuler')}>Annuler</button>}
        </div>
      )}
    </article>
  )
}
