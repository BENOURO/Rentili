import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import ReviewCard from '../components/reviews/ReviewCard'
import ReviewForm from '../components/reviews/ReviewForm'
import ReviewHero from '../components/reviews/ReviewHero'
import ReviewToolbar from '../components/reviews/ReviewToolbar'
import { useAuth } from '../auth/AuthContext'
import {
  createAvis,
  deleteAvis,
  getAvis,
  getEligibleAvis,
  updateAvis,
} from '../services/avisService'

const emptyForm = {
  utilisateur_id: 1,
  annonce_id: '',
  reservation_id: '',
  rating: 5,
  comment: '',
}

export default function AvisPage() {
  const { user } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()
  const [reviews, setReviews] = useState([])
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all')
  const [editingId, setEditingId] = useState(null)
  const [error, setError] = useState('')
  const [eligibleReservations, setEligibleReservations] = useState([])
  const [form, setForm] = useState({
    ...emptyForm,
    utilisateur_id: user?.id ?? emptyForm.utilisateur_id,
  })

  const listerAvis = useCallback(async () => {
    try {
      setReviews(await getAvis())
    } catch (loadError) {
      setError(loadError.message)
    }
  }, [])

  useEffect(() => {
    Promise.resolve().then(listerAvis)
  }, [listerAvis])

  useEffect(() => {
    if (!user) {
      setEligibleReservations([])
      return
    }
    getEligibleAvis()
      .then((eligible) => {
        setEligibleReservations(eligible)
        const reservationId = Number(searchParams.get('reservation'))
        const annonceId = Number(searchParams.get('annonce'))
        if (reservationId && eligible.some((item) => item.reservation_id === reservationId)) {
          setForm((current) => ({
            ...current,
            reservation_id: String(reservationId),
            annonce_id: annonceId || current.annonce_id,
            utilisateur_id: user.id,
          }))
          window.requestAnimationFrame(() => {
            document.querySelector('#ajouter')?.scrollIntoView({ behavior: 'smooth' })
          })
        }
      })
      .catch(() => setEligibleReservations([]))
  }, [user, searchParams])

  const objectReviews = useMemo(() => {
    const selectedAnnonceId = Number(searchParams.get('annonce'))
    return selectedAnnonceId
      ? reviews.filter((review) => review.annonce_id === selectedAnnonceId)
      : reviews
  }, [reviews, searchParams])

  const visibleReviews = useMemo(() => objectReviews.filter((review) => {
    const matchesSearch = `${review.item} ${review.owner} ${review.comment}`
      .toLowerCase()
      .includes(search.toLowerCase())
    const matchesFilter =
      filter === 'all' ||
      (filter === 'positive' && review.rating >= 4) ||
      (filter === 'low' && review.rating <= 3)
    return matchesSearch && matchesFilter
  }), [objectReviews, search, filter])

  const average = objectReviews.length
    ? (objectReviews.reduce((total, review) => total + review.rating, 0) / objectReviews.length).toFixed(1)
    : '0.0'

  function resetForm() {
    setEditingId(null)
    setForm({
      ...emptyForm,
      utilisateur_id: user?.id ?? emptyForm.utilisateur_id,
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
      if (editingId) await updateAvis(editingId, payload)
      else await createAvis(payload)
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
    window.requestAnimationFrame(() => {
      document.querySelector('#ajouter')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      window.setTimeout(() => document.querySelector('#comment')?.focus(), 350)
    })
  }

  async function deleteReview(id) {
    setError('')
    try {
      await deleteAvis(id)
      await listerAvis()
      if (editingId === id) resetForm()
    } catch (deleteError) {
      setError(deleteError.message)
    }
  }

  return (
    <>
      <ReviewHero
        reviewCount={objectReviews.length}
        average={average}
        positiveCount={objectReviews.filter((review) => review.rating >= 4).length}
      />

      <section className="page" id="avis">
          <div className="wrap">
            <div className="page-head">
              <div>
                <p className="eyebrow">Communauté</p>
                <h1>Les avis des locataires</h1>
              </div>
              <button
                className="btn"
                type="button"
                onClick={() => document.querySelector('#ajouter')?.scrollIntoView({ behavior: 'smooth' })}
                disabled={!editingId && eligibleReservations.length === 0}
              >
                + Ajouter un avis
              </button>
            </div>

            <ReviewToolbar
              search={search}
              filter={filter}
              onSearchChange={setSearch}
              onFilterChange={setFilter}
            />

            {searchParams.get('annonce') && (
              <div className="review-toolbar card">
                <strong>
                  Avis pour : {
                    visibleReviews[0]?.item ??
                    reviews.find((review) => review.annonce_id === Number(searchParams.get('annonce')))?.item ??
                    `Objet ${searchParams.get('annonce')}`
                  }
                </strong>
                <button
                  className="btn ghost sm"
                  type="button"
                  onClick={() => setSearchParams({})}
                >
                  Voir tous les objets
                </button>
              </div>
            )}

            {error && <div className="alert" role="alert">{error}</div>}

            {visibleReviews.length ? (
              <div className="review-grid">
                {visibleReviews.map((review) => (
                  <ReviewCard
                    key={review.id}
                    review={review}
                    canManage={Boolean(user && review.utilisateur_id === user.id)}
                    onEdit={editReview}
                    onDelete={deleteReview}
                  />
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

      <ReviewForm
        editingId={editingId}
        form={form}
        eligibleReservations={eligibleReservations}
        onChange={setForm}
        onSubmit={handleSubmit}
        onReset={resetForm}
      />
    </>
  )
}
