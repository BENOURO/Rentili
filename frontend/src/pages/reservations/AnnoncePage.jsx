import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../../api/client'
import ContactButton from '../messaging/ContactButton'
import { dt, periode } from './format'
import ReservationForm from './ReservationForm'
import './reservations.css'

/** Détail d'un objet et formulaire de demande de réservation (US21). */
export default function AnnoncePage() {
  const { id } = useParams()
  const [annonce, setAnnonce] = useState(undefined)

  useEffect(() => {
    api(`/reservations/annonces/${id}/`).then(setAnnonce).catch(() => setAnnonce(null))
  }, [id])

  if (annonce === undefined) return <div className="wrap page"><p className="muted">Chargement…</p></div>
  if (annonce === null) return <div className="wrap page"><div className="empty"><h3>Objet introuvable</h3><Link to="/annonces">Retour aux objets</Link></div></div>

  return (
    <div className="wrap page">
      <p className="small"><Link className="muted" to="/annonces">← Tous les objets</Link></p>
      <div className="annonce-layout">
        <div className="card">
          {annonce.categorie && <span className="tag">{annonce.categorie}</span>}
          <h1 style={{ marginTop: 10 }}>{annonce.titre}</h1>
          <p className="muted">{annonce.ville} · proposé par <Link to={`/membres/${annonce.proprietaire.id}`}>{annonce.proprietaire.display_name}</Link></p>
          <div className="facts">
            <div className="fact"><span className="muted small">Prix</span><b>{dt(annonce.prix_jour)}</b><span className="muted small">par jour</span></div>
            <div className="fact"><span className="muted small">Caution</span><b>{dt(annonce.caution)}</b><span className="muted small">rendue au retour</span></div>
            <div className="fact"><span className="muted small">Ville</span><b>{annonce.ville || '—'}</b></div>
          </div>
          {annonce.description && <p className="pre">{annonce.description}</p>}
          <h3>Disponibilités</h3>
          {annonce.periodes_reservees.length === 0
            ? <p className="muted small">Aucune période réservée pour le moment : l'objet est libre.</p>
            : (
              <>
                <p className="muted small" style={{ margin: 0 }}>Déjà réservé :</p>
                <ul className="periodes">{annonce.periodes_reservees.map((p) => <li key={p.date_debut}>{periode(p.date_debut, p.date_fin)}</li>)}</ul>
              </>
            )}
          <div style={{ marginTop: 20 }}>
            <ContactButton listingId={annonce.id} listingTitle={annonce.titre} ownerId={annonce.proprietaire.id} />
          </div>
        </div>
        <ReservationForm annonce={annonce} />
      </div>
    </div>
  )
}
