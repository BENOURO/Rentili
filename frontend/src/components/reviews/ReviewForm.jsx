import { announcements, users } from '../../data/catalog'
import StarRating from './StarRating'

export default function ReviewForm({ editingId, form, onChange, onSubmit, onReset }) {
  return (
    <section className="page review-form-section" id="ajouter">
      <div className="wrap narrow">
        <div className="card">
          <h2>{editingId ? 'Modifier votre avis' : 'Partager votre expérience'}</h2>
          <p className="muted">Votre avis aide les membres de la communauté.</p>
          <form onSubmit={onSubmit}>
            <div className="grid-2">
              <div className="field">
                <label htmlFor="annonce">Annonce <span className="req">*</span></label>
                <select
                  id="annonce"
                  className="input"
                  value={form.annonce_id}
                  onChange={(event) => onChange({ ...form, annonce_id: event.target.value })}
                  required
                >
                  {announcements.map((announcement) => (
                    <option key={announcement.id} value={announcement.id}>{announcement.name}</option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label htmlFor="utilisateur">Utilisateur <span className="req">*</span></label>
                <select
                  id="utilisateur"
                  className="input"
                  value={form.utilisateur_id}
                  onChange={(event) => onChange({ ...form, utilisateur_id: event.target.value })}
                  required
                >
                  {users.map((user) => (
                    <option key={user.id} value={user.id}>{user.name}</option>
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
                onChange={(event) => onChange({ ...form, reservation_id: event.target.value })}
                required
              />
            </div>
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
          </form>
        </div>
      </div>
    </section>
  )
}
