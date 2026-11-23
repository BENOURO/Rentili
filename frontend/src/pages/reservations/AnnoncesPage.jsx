import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../../api/client'
import { dt } from './format'
import { useAuth } from '../../auth/AuthContext'
import Field from '../../components/Field'
import './reservations.css'

export default function AnnoncesPage() {
  const { user } = useAuth()
  const [params, setParams] = useSearchParams()
  const [data, setData] = useState(null)
  const [categories, setCategories] = useState([])
  const filters = Object.fromEntries(params.entries())

  useEffect(() => {
    api('/reservations/annonces/categories/').then(setCategories).catch(() => setCategories([]))
  }, [])

  useEffect(() => {
    const q = new URLSearchParams(params)
    api(`/reservations/annonces/?${q}`).then(setData).catch(() => setData({ count: 0, results: [] }))
  }, [params])

  const setFilter = (e) => {
    const next = new URLSearchParams(params)
    if (e.target.value) next.set(e.target.name, e.target.value)
    else next.delete(e.target.name)
    next.delete('page')
    setParams(next)
  }

  const chargerPage = (page) => {
    const next = new URLSearchParams(params)
    next.set('page', String(page))
    setParams(next)
  }

  return (
    <div className="wrap page">
      <div className="page-head">
        <div><h1>Objets à louer</h1><p className="muted" style={{ margin: 0 }}>Choisissez un objet puis demandez une réservation pour vos dates.</p></div>
        {user && <Link className="btn" to="/annonces/publier">Publier une annonce</Link>}
      </div>
      <div className="card annonce-filters">
        <div className="grid-2">
          <Field label="Recherche" name="search" value={filters.search || ''} onChange={setFilter} placeholder="Titre ou description" />
          <Field label="Catégorie" name="categorie" as="select" value={filters.categorie || ''} onChange={setFilter}>
            <option value="">Toutes</option>
            {categories.map((c) => <option key={c.id} value={c.id}>{c.nom}</option>)}
          </Field>
        </div>
        <div className="grid-2">
          <Field label="Ville" name="ville" value={filters.ville || ''} onChange={setFilter} />
          <div className="grid-2">
            <Field label="Prix min." name="prix_min" type="number" min="0" value={filters.prix_min || ''} onChange={setFilter} />
            <Field label="Prix max." name="prix_max" type="number" min="0" value={filters.prix_max || ''} onChange={setFilter} />
          </div>
        </div>
        <div className="grid-2">
          <Field label="Disponible du" name="date_debut" type="date" value={filters.date_debut || ''} onChange={setFilter} />
          <Field label="Au" name="date_fin" type="date" value={filters.date_fin || ''} onChange={setFilter} />
        </div>
      </div>
      {data === null ? <p className="muted">Chargement…</p>
        : data.results.length === 0 ? <div className="empty"><h3>Aucun objet pour le moment</h3><p>Lancez <code>python manage.py seed_reservations</code> pour créer des annonces de démonstration.</p></div>
        : (
          <>
          <div className="annonce-grid">
            {data.results.map((a) => (
              <Link key={a.id} to={`/annonces/${a.id}`} className="card annonce-card">
                {a.photos?.[0] ? <img className="annonce-cover" src={a.photos[0].image} alt="" /> : <div className="annonce-cover placeholder">RENTILI</div>}
                {a.categorie && <span className="tag">{a.categorie.nom}</span>}
                <h3>{a.titre}</h3>
                <span className="muted small">{a.ville} · proposé par {a.proprietaire.display_name}</span>
                <span className="prix">{dt(a.prix_jour)} <span className="muted small">/ jour</span></span>
              </Link>
            ))}
          </div>
          {data.count > data.results.length && <div className="pager">
            {data.previous && <button className="btn ghost" onClick={() => chargerPage(Math.max(1, Number(params.get('page') || 1) - 1))}>Précédent</button>}
            <span className="muted small">Page {params.get('page') || 1}</span>
            {data.next && <button className="btn ghost" onClick={() => chargerPage(Number(params.get('page') || 1) + 1)}>Suivant</button>}
          </div>}
          </>
        )}
    </div>
  )
}
