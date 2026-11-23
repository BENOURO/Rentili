import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import { dt } from './format'
import './reservations.css'

/** Liste des objets à louer (version minimale en attendant le module « Gestion des annonces »). */
export default function AnnoncesPage() {
  const [data, setData] = useState(null)

  useEffect(() => {
    api('/reservations/annonces/').then(setData).catch(() => setData({ count: 0, results: [] }))
  }, [])

  return (
    <div className="wrap page">
      <div className="page-head">
        <div><h1>Objets à louer</h1><p className="muted" style={{ margin: 0 }}>Choisissez un objet puis demandez une réservation pour vos dates.</p></div>
      </div>
      {data === null ? <p className="muted">Chargement…</p>
        : data.results.length === 0 ? <div className="empty"><h3>Aucun objet pour le moment</h3><p>Lancez <code>python manage.py seed_reservations</code> pour créer des annonces de démonstration.</p></div>
        : (
          <div className="annonce-grid">
            {data.results.map((a) => (
              <Link key={a.id} to={`/annonces/${a.id}`} className="card annonce-card">
                {a.categorie && <span className="tag">{a.categorie}</span>}
                <h3>{a.titre}</h3>
                <span className="muted small">{a.ville} · proposé par {a.proprietaire.display_name}</span>
                <span className="prix">{dt(a.prix_jour)} <span className="muted small">/ jour</span></span>
              </Link>
            ))}
          </div>
        )}
    </div>
  )
}
