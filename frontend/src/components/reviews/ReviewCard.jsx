import StarRating from './StarRating'

export default function ReviewCard({ review, onEdit, onDelete }) {
  const initials = review.owner.split(' ').map((name) => name[0]).join('').slice(0, 2)

  return (
    <article className="review-card card">
      <div className="review-card-head">
        <div className="avatar md" aria-hidden="true">{initials}</div>
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
          <button className="btn ghost sm" type="button" onClick={() => onEdit(review)}>Modifier</button>
          <button className="btn danger sm" type="button" onClick={() => onDelete(review.id)}>Supprimer</button>
        </div>
      </div>
    </article>
  )
}
