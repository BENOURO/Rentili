import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../../api/client'
import Field from '../../components/Field'
import { useToast } from '../../components/Toast'
import './reservations.css'

export default function AnnonceFormPage({ mode = 'create' }) {
  const { id } = useParams()
  const navigate = useNavigate()
  const notify = useToast()
  const editing = mode === 'edit'
  const [categories, setCategories] = useState([])
  const [form, setForm] = useState({ titre: '', description: '', categorie_id: '', ville: '', prix_jour: '', caution: '0' })
  const [photos, setPhotos] = useState([])
  const [previews, setPreviews] = useState([])
  const [errors, setErrors] = useState({})
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api('/reservations/annonces/categories/').then(setCategories).catch(() => setCategories([]))
  }, [])

  useEffect(() => {
    if (!editing) return
    api(`/reservations/annonces/${id}/`).then((a) => setForm({
      titre: a.titre, description: a.description, categorie_id: a.categorie?.id || '',
      ville: a.ville, prix_jour: a.prix_jour, caution: a.caution,
    })).catch(() => navigate('/annonces'))
  }, [editing, id, navigate])

  const set = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  function onPhotos(e) {
    const files = Array.from(e.target.files || []).slice(0, 8)
    setPhotos(files)
    setPreviews(files.map((file) => URL.createObjectURL(file)))
  }

  async function onSubmit(e) {
    e.preventDefault()
    setBusy(true); setErrors({})
    const body = new FormData()
    Object.entries(form).forEach(([key, value]) => body.append(key, value))
    photos.forEach((photo) => body.append('photos', photo))
    try {
      const annonce = await api(`/reservations/annonces/${editing ? `${id}/` : ''}`, {
        method: editing ? 'PATCH' : 'POST',
        body,
      })
      notify(editing ? 'Annonce mise à jour.' : 'Annonce publiée.')
      navigate(`/annonces/${annonce.id}`)
    } catch (err) {
      setErrors(Object.keys(err.fields).length ? err.fields : { non_field_errors: [err.message] })
    } finally { setBusy(false) }
  }

  return (
    <div className="wrap page"><div className="narrow">
      <p><Link className="muted" to="/annonces">← Retour aux objets</Link></p>
      <h1>{editing ? 'Modifier mon annonce' : 'Publier une annonce'}</h1>
      <form className="card" onSubmit={onSubmit} noValidate>
        {errors.non_field_errors && <div className="alert">{errors.non_field_errors.join(' ')}</div>}
        <Field label="Titre" name="titre" value={form.titre} onChange={set} errors={errors} required maxLength={120} placeholder="Ex. Perceuse-visseuse Bosch 18V" />
        <Field label="Description" name="description" as="textarea" rows={5} value={form.description} onChange={set} errors={errors} required placeholder="Décrivez l'objet, son état et les accessoires inclus." />
        <div className="grid-2">
          <Field label="Catégorie" name="categorie_id" as="select" value={form.categorie_id} onChange={set} errors={errors}>
            <option value="">Choisir une catégorie</option>
            {categories.map((c) => <option key={c.id} value={c.id}>{c.nom}</option>)}
          </Field>
          <Field label="Ville" name="ville" value={form.ville} onChange={set} errors={errors} required placeholder="Tunis" />
        </div>
        <div className="grid-2">
          <Field label="Prix par jour (DT)" name="prix_jour" type="number" min="0" step="0.01" value={form.prix_jour} onChange={set} errors={errors} required />
          <Field label="Caution (DT)" name="caution" type="number" min="0" step="0.01" value={form.caution} onChange={set} errors={errors} required />
        </div>
        <div className="field">
          <label htmlFor="photos">Photos {editing ? '(remplacera les photos actuelles)' : ''}</label>
          <input id="photos" name="photos" type="file" accept="image/*" multiple onChange={onPhotos} />
          {errors.photos && <div className="err">{errors.photos.join(' ')}</div>}
          {previews.length > 0 && <div className="photo-previews">{previews.map((src, i) => <img key={src} src={src} alt={`Aperçu ${i + 1}`} />)}</div>}
        </div>
        <div className="row between">
          <Link className="muted" to="/annonces">Annuler</Link>
          <button className="btn" disabled={busy}>{busy ? 'Enregistrement…' : editing ? 'Mettre à jour' : 'Publier l’annonce'}</button>
        </div>
      </form>
    </div></div>
  )
}
