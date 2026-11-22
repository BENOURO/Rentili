import { useCallback, useEffect, useMemo, useState } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import './App.css'

const users = [
  { id: 1, name: 'Amine Bennour' },
  { id: 2, name: 'Ghassen Barhoumi' },
  { id: 3, name: 'Youssef Marzouki' },
  { id: 4, name: 'Ghayth Ben Othmen' },
]

const announcements = [
  { id: 1, name: 'Canon EOS 2000D' },
  { id: 2, name: 'Tente familiale 4 places' },
  { id: 3, name: 'Perceuse-visseuse' },
  { id: 4, name: 'Vélo électrique' },
]

function StarRating({ rating, interactive = false, onChange }) {
  return (
    <div className="stars" aria-label={`Note : ${rating} sur 5`}>
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          type="button"
          key={star}
          className={star <= rating ? 'star active' : 'star'}
          disabled={!interactive}
          onClick={() => interactive && onChange(star)}
          aria-label={`${star} étoile${star > 1 ? 's' : ''}`}
        >
          ★
        </button>
      ))}
    </div>
  )
}

function mapAvis(avis) {
  const utilisateur = users.find((user) => user.id === avis.utilisateur_id)
  const annonce = announcements.find((item) => item.id === avis.annonce_id)

  return {
    id: avis.idAvis,
    utilisateur_id: avis.utilisateur_id,
    annonce_id: avis.annonce_id,
    reservation_id: avis.reservation_id,
    item: annonce?.name ?? `Annonce ${avis.annonce_id}`,
    owner: utilisateur?.name ?? `Utilisateur ${avis.utilisateur_id}`,
    rating: avis.note,
    comment: avis.commentaire,
    date: new Intl.DateTimeFormat('fr-FR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    }).format(new Date(avis.dateAvis)),
  }
}

function AvisPage() {
  const [reviews, setReviews] = useState([])
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all')
  const [editingId, setEditingId] = useState(null)
  const [error, setError] = useState('')
  const [form, setForm] = useState({
    utilisateur_id: 1,
    annonce_id: 1,
    reservation_id: 1,
    rating: 5,
    comment: '',
  })

  const listerAvis = useCallback(async () => {
    try {
      const response = await fetch('/api/avis/')
      if (!response.ok) throw new Error('Impossible de charger les avis')
      const data = await response.json()
      setReviews(data.map(mapAvis))
    } catch (loadError) {
      setError(loadError.message)
    }
  }, [])

  useEffect(() => {
    Promise.resolve().then(listerAvis)
  }, [listerAvis])

  const visibleReviews = useMemo(() => {
    return reviews.filter((review) => {
      const matchesSearch = `${review.item} ${review.owner} ${review.comment}`
        .toLowerCase()
        .includes(search.toLowerCase())
      const matchesFilter =
        filter === 'all' ||
        (filter === 'positive' && review.rating >= 4) ||
        (filter === 'low' && review.rating <= 3)
      return matchesSearch && matchesFilter
    })
  }, [reviews, search, filter])

  const average = reviews.length
    ? (reviews.reduce((total, review) => total + review.rating, 0) / reviews.length).toFixed(1)
    : '0.0'

  function resetForm() {
    setEditingId(null)
    setForm({
      utilisateur_id: 1,
      annonce_id: 1,
      reservation_id: 1,
      rating: 5,
      comment: '',
    })
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (!form.comment.trim()) return

    setError('')
    const payload = {
      utilisateur_id: Number(form.utilisateur_id),
      annonce_id: Number(form.annonce_id),
      reservation_id: Number(form.reservation_id),
      note: Number(form.rating),
      commentaire: form.comment.trim(),
    }

    try {
      const response = await fetch(
        editingId ? `/api/avis/${editingId}/` : '/api/avis/',
        {
          method: editingId ? 'PATCH' : 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        },
      )
      if (!response.ok) {
        const details = await response.json()
        throw new Error(JSON.stringify(details))
      }
      await listerAvis()
      resetForm()
    } catch (submitError) {
      setError(submitError.message)
    }
  }

  function editReview(review) {
    setEditingId(review.id)
    setForm({
      utilisateur_id: review.utilisateur_id,
      annonce_id: review.annonce_id,
      reservation_id: review.reservation_id,
      rating: review.rating,
      comment: review.comment,
    })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  async function deleteReview(id) {
    setError('')
    try {
      const response = await fetch(`/api/avis/${id}/`, { method: 'DELETE' })
      if (!response.ok) throw new Error('Impossible de supprimer cet avis')
      await listerAvis()
      if (editingId === id) resetForm()
    } catch (deleteError) {
      setError(deleteError.message)
    }
  }

  return (
    <>
      <nav className="nav">
        <div className="wrap">
          <a className="logo" href="/" aria-label="Rentili accueil">
            <span className="logo-mark" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none">
                <path d="M4 20V8l8-4 8 4v12M8 20v-7h8v7M3 20h18" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </span>
            <span className="logo-text">Rentili</span>
          </a>
          <div className="nav-links">
            <a href="#avis">Avis</a>
            <a href="#ajouter">Ajouter un avis</a>
            <button className="avatar" type="button" aria-label="Profil utilisateur">AB</button>
          </div>
        </div>
      </nav>

      <main>
        <section className="review-hero">
          <div className="hero-deco" />
          <div className="wrap">
            <p className="eyebrow">Avis & communauté</p>
            <h1>Des locations <em>bien notées</em>, des expériences fiables.</h1>
            <p className="lead">
              Consultez les avis, partagez votre expérience et faites confiance à la communauté Rentili.
            </p>
            <div className="hero-stats">
              <span><b>{reviews.length}</b> avis publiés</span>
              <span><b>{average}/5</b> note moyenne</span>
              <span><b>{reviews.filter((review) => review.rating >= 4).length}</b> avis positifs</span>
            </div>
          </div>
        </section>

        <section className="page" id="avis">
          <div className="wrap">
            <div className="page-head">
              <div>
                <p className="eyebrow">Communauté</p>
                <h1>Les avis des locataires</h1>
              </div>
              <button className="btn" type="button" onClick={() => document.querySelector('#ajouter')?.scrollIntoView({ behavior: 'smooth' })}>
                + Ajouter un avis
              </button>
            </div>

            <div className="review-toolbar card">
              <input
                className="input search"
                type="search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Rechercher un objet ou un avis"
              />
              <div className="filter-buttons" aria-label="Filtrer les avis">
                <button className={filter === 'all' ? 'filter active' : 'filter'} type="button" onClick={() => setFilter('all')}>Tous</button>
                <button className={filter === 'positive' ? 'filter active' : 'filter'} type="button" onClick={() => setFilter('positive')}>Positifs</button>
                <button className={filter === 'low' ? 'filter active' : 'filter'} type="button" onClick={() => setFilter('low')}>À améliorer</button>
              </div>
            </div>

            {error && <div className="alert" role="alert">{error}</div>}

            {visibleReviews.length ? (
              <div className="review-grid">
                {visibleReviews.map((review) => (
                  <article className="review-card card" key={review.id}>
                    <div className="review-card-head">
                      <div className="avatar md" aria-hidden="true">
                        {review.owner.split(' ').map((name) => name[0]).join('').slice(0, 2)}
                      </div>
                      <div className="grow">
                        <h3>{review.item}</h3>
                        <p className="small muted">Loué auprès de {review.owner}</p>
                      </div>
                      <StarRating rating={review.rating} />
                    </div>
                    <p className="pre review-comment">{review.comment}</p>
                    <div className="review-card-foot">
                      <span className="small muted">{review.date}</span>
                      <div className="row">
                        <button className="btn ghost sm" type="button" onClick={() => editReview(review)}>Modifier</button>
                        <button className="btn danger sm" type="button" onClick={() => deleteReview(review.id)}>Supprimer</button>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <div className="empty">
                <h3>Aucun avis trouvé</h3>
                <p>Modifiez votre recherche ou ajoutez un nouvel avis.</p>
              </div>
            )}
          </div>
        </section>

        <section className="page review-form-section" id="ajouter">
          <div className="wrap narrow">
            <div className="card">
              <h2>{editingId ? 'Modifier votre avis' : 'Partager votre expérience'}</h2>
              <p className="muted">Votre avis aide les membres de la communauté.</p>
              <form onSubmit={handleSubmit}>
                <div className="grid-2">
                  <div className="field">
                    <label htmlFor="annonce">Annonce <span className="req">*</span></label>
                    <select
                      id="annonce"
                      className="input"
                      value={form.annonce_id}
                      onChange={(event) => setForm({ ...form, annonce_id: event.target.value })}
                      required
                    >
                      {announcements.map((announcement) => (
                        <option key={announcement.id} value={announcement.id}>
                          {announcement.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="field">
                    <label htmlFor="utilisateur">Utilisateur <span className="req">*</span></label>
                    <select
                      id="utilisateur"
                      className="input"
                      value={form.utilisateur_id}
                      onChange={(event) => setForm({ ...form, utilisateur_id: event.target.value })}
                      required
                    >
                      {users.map((user) => (
                        <option key={user.id} value={user.id}>
                          {user.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="field">
                  <label htmlFor="reservation">Réservation <span className="req">*</span></label>
                  <input
                    id="reservation"
                    className="input"
                    type="number"
                    min="1"
                    value={form.reservation_id}
                    onChange={(event) => setForm({ ...form, reservation_id: event.target.value })}
                    required
                  />
                </div>
                <div className="field">
                  <label>Note <span className="req">*</span></label>
                  <StarRating
                    rating={form.rating}
                    interactive
                    onChange={(rating) => setForm({ ...form, rating })}
                  />
                </div>
                <div className="field">
                  <label htmlFor="comment">Commentaire <span className="req">*</span></label>
                  <textarea
                    id="comment"
                    className="input"
                    rows="5"
                    value={form.comment}
                    onChange={(event) => setForm({ ...form, comment: event.target.value })}
                    placeholder="Décrivez votre expérience..."
                    required
                  />
                </div>
                <div className="row">
                  <button className="btn" type="submit">
                    {editingId ? 'Enregistrer les modifications' : 'Publier l’avis'}
                  </button>
                  {editingId && (
                    <button className="btn ghost" type="button" onClick={resetForm}>Annuler</button>
                  )}
                </div>
              </form>
            </div>
          </div>
        </section>
      </main>

      <footer className="foot">
        <div className="wrap">
          <strong>Rentili</strong> · Louer simplement, partout.
        </div>
      </footer>
    </>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/avis" element={<AvisPage />} />
      <Route path="/" element={<Navigate to="/avis" replace />} />
      <Route path="*" element={<Navigate to="/avis" replace />} />
    </Routes>
  )
}
