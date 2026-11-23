import StarRating from './StarRating'

export default function ReviewForm({ editingId, form, eligibleReservations, onChange, onSubmit, onReset }) {
  const selectedReservation = eligibleReservations.find(
    (item) => item.reservation_id === Number(form.reservation_id),
  )

  if (!editingId && !selectedReservation) return null

  return (
    <section className="page review-form-section" id="ajouter">
      <div className="wrap narrow">
        <div className="card">
          <h2>{editingId ? 'Modifier votre avis' : 'Partager votre expérience'}</h2>
          <p className="muted">Votre avis aide les membres de la communauté.</p>
          <form onSubmit={onSubmit}>
            {!editingId && (
              <div className="field">
                <label htmlFor="objet">Objet loué <span className="req">*</span></label>
                <select
                  id="objet"
                  className="input"
                  value={form.reservation_id}
                  onChange={(event) => {
                    const selected = eligibleReservations.find(
                      (item) => item.reservation_id === Number(event.target.value),
                    )
                    onChange({
                      ...form,
                      reservation_id: event.target.value,
                      annonce_id: selected?.annonce_id ?? '',
                    })
                  }}
                  required
                >
                  <option value="">Sélectionner un objet</option>
                  {eligibleReservations.map((item) => (
                    <option key={item.reservation_id} value={item.reservation_id}>
                      {item.annonce_titre}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {(editingId || selectedReservation) && (
              <>
                <div className="field">
                  <label>Note <span className="req">*</span></label>
                  <StarRating rating={form.rating} interactive onChange={(rating) => onChange({ ...form, rating })} />
                </div>
                <div className="field">
                  <label htmlFor="comment">Commentaire <span className="req">*</span></label>
                  <textarea
                    id="comment"
                    className="input"
                    rows="5"
                    value={form.comment}
                    onChange={(event) => onChange({ ...form, comment: event.target.value })}
                    placeholder="Décrivez votre expérience..."
                    required
                  />
                </div>
                <div className="row">
                  <button className="btn" type="submit">
                    {editingId ? 'Enregistrer les modifications' : 'Publier l’avis'}
                  </button>
                  {editingId && (
                    <button className="btn ghost" type="button" onClick={onReset}>Annuler</button>
                  )}
                </div>
              </>
            )}
          </form>
        </div>
      </div>
    </section>
  )
}
