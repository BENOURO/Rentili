export default function StarRating({ rating, interactive = false, onChange }) {
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
