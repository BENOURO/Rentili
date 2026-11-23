import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../../api/client'
import { STATUTS } from './format'
import ReservationCard from './ReservationCard'
import './reservations.css'

const VUES = {
  envoyees: { role: 'locataire', titre: 'Mes demandes', vide: "Vous n'avez encore rien réservé." },
  recues: { role: 'proprietaire', titre: 'Demandes reçues', vide: "Personne n'a encore demandé vos objets." },
}

/** US23 — Consulter mes réservations (envoyées en tant que locataire, reçues en tant que propriétaire) et leur statut. */
export default function MesReservationsPage() {
  const [params, setParams] = useSearchParams()
  const vue = params.get('vue') === 'recues' ? 'recues' : 'envoyees'
  const statut = params.get('statut') || ''
  const [list, setList] = useState(null)

  useEffect(() => {
    let actif = true
    const q = new URLSearchParams({ role: VUES[vue].role })
    if (statut) q.set('statut', statut)
    api(`/reservations/?${q}`).then((d) => actif && setList(d)).catch(() => actif && setList([]))
    return () => { actif = false }
  }, [vue, statut])

  const choisir = (v, s = '') => { setList(null); setParams(s ? { vue: v, statut: s } : { vue: v }) }
  const remplacer = (r) => setList((l) => l.map((x) => (x.id === r.id ? r : x)))

  return (
    <div className="wrap page">
      <div className="page-head">
        <div><h1>Mes réservations</h1><p className="muted" style={{ margin: 0 }}>Suivez vos demandes et gérez celles que vous recevez pour vos objets.</p></div>
        <Link className="btn" to="/annonces">Réserver un objet</Link>
      </div>
      <div className="tabs" role="tablist">
        {Object.entries(VUES).map(([k, v]) => (
          <button key={k} role="tab" aria-selected={vue === k} className={vue === k ? 'on' : ''} onClick={() => choisir(k)}>{v.titre}</button>
        ))}
      </div>
      <div className="filtres">
        <button className={!statut ? 'on' : ''} onClick={() => choisir(vue)}>Toutes</button>
        {Object.entries(STATUTS).map(([k, s]) => (
          <button key={k} className={statut === k ? 'on' : ''} onClick={() => choisir(vue, k)}>{s.label}</button>
        ))}
      </div>
      {list === null ? <p className="muted">Chargement…</p>
        : list.length === 0 ? <div className="empty"><h3>{statut ? 'Aucune réservation avec ce statut' : VUES[vue].vide}</h3></div>
        : <div className="resa-list">{list.map((r) => <ReservationCard key={r.id} resa={r} onChange={remplacer} />)}</div>}
    </div>
  )
}
