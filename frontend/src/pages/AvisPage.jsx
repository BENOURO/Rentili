import { useCallback, useEffect, useMemo, useState } from 'react'
import Footer from '../components/layout/Footer'
import Navbar from '../components/layout/Navbar'
import ReviewCard from '../components/reviews/ReviewCard'
import ReviewForm from '../components/reviews/ReviewForm'
import ReviewHero from '../components/reviews/ReviewHero'
import ReviewToolbar from '../components/reviews/ReviewToolbar'
import { createAvis, deleteAvis, getAvis, updateAvis } from '../services/avisService'

const emptyForm = {
  utilisateur_id: 1,
  annonce_id: 1,
  reservation_id: 1,
  rating: 5,
  comment: '',
}

export default function AvisPage() {
  const [reviews, setReviews] = useState([])
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all')
  const [editingId, setEditingId] = useState(null)
  const [error, setError] = useState('')
  const [form, setForm] = useState(emptyForm)

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

  const visibleReviews = useMemo(() => reviews.filter((review) => {
    const matchesSearch = `${review.item} ${review.owner} ${review.comment}`
      .toLowerCase()
      .includes(search.toLowerCase())
    const matchesFilter =
      filter === 'all' ||
      (filter === 'positive' && review.rating >= 4) ||
      (filter === 'low' && review.rating <= 3)
    return matchesSearch && matchesFilter
  }), [reviews, search, filter])

  const average = reviews.length
    ? (reviews.reduce((total, review) => total + review.rating, 0) / reviews.length).toFixed(1)
    : '0.0'

  function resetForm() {
    setEditingId(null)
    setForm(emptyForm)
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
    window.scrollTo({ top: 0, behavior: 'smooth' })
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
      <Navbar />
      <main>
        <ReviewHero
          reviewCount={reviews.length}
          average={average}
          positiveCount={reviews.filter((review) => review.rating >= 4).length}
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

            {error && <div className="alert" role="alert">{error}</div>}

            {visibleReviews.length ? (
              <div className="review-grid">
                {visibleReviews.map((review) => (
                  <ReviewCard
                    key={review.id}
                    review={review}
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
          onChange={setForm}
          onSubmit={handleSubmit}
          onReset={resetForm}
        />
      </main>
      <Footer />
    </>
  )
}
