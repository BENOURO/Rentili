import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import Avatar from '../../components/Avatar'
import Field from '../../components/Field'
import { useToast } from '../../components/Toast'

/** US04 — Modifier son profil (photo envoyée en multipart). */
export default function EditProfilePage() {
  const { user, setUser } = useAuth()
  const notify = useToast()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    first_name: user.first_name, last_name: user.last_name, phone: user.phone, city: user.city, bio: user.bio,
  })
  const [avatar, setAvatar] = useState(null)
  const [preview, setPreview] = useState(null)
  const [errors, setErrors] = useState({})
  const [busy, setBusy] = useState(false)
  const set = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  function onAvatar(e) {
    const file = e.target.files[0]
    setAvatar(file || null)
    setPreview(file ? URL.createObjectURL(file) : null)
  }

  async function onSubmit(e) {
    e.preventDefault()
    setBusy(true); setErrors({})
    const body = new FormData()
    Object.entries(form).forEach(([k, v]) => body.append(k, v ?? ''))
    if (avatar) body.append('avatar', avatar)
    try {
      setUser(await api('/users/me/', { method: 'PATCH', body }))
      notify('Profil mis à jour.')
      navigate('/profil')
    } catch (err) {
      setErrors(err.fields)
    } finally { setBusy(false) }
  }

  return (
    <div className="wrap page"><div className="narrow">
      <h1>Modifier mon profil</h1>
      <form className="card" onSubmit={onSubmit} noValidate>
        <div className="row" style={{ marginBottom: 18 }}>
          {preview ? <span className="avatar lg"><img src={preview} alt="" /></span> : <Avatar user={user} size="lg" />}
          <div className="field grow" style={{ margin: 0 }}>
            <label htmlFor="avatar">Photo de profil</label>
            <input id="avatar" type="file" accept="image/*" onChange={onAvatar} />
            {errors.avatar && <div className="err">{errors.avatar.join(' ')}</div>}
          </div>
        </div>
        <div className="grid-2">
          <Field label="Prénom" name="first_name" value={form.first_name} onChange={set} errors={errors} required />
          <Field label="Nom" name="last_name" value={form.last_name} onChange={set} errors={errors} required />
        </div>
        <div className="grid-2">
          <Field label="Ville" name="city" value={form.city} onChange={set} errors={errors} />
          <Field label="Téléphone" name="phone" value={form.phone} onChange={set} errors={errors} placeholder="+216 …" />
        </div>
        <Field label="Présentation" name="bio" as="textarea" rows={4} value={form.bio} onChange={set} errors={errors}
          help="Quelques mots sur vous : ce que vous louez, ce que vous cherchez." maxLength={500} />
        <div className="row between">
          <Link className="muted" to="/profil">Annuler</Link>
          <button className="btn" disabled={busy}>{busy ? 'Enregistrement…' : 'Enregistrer'}</button>
        </div>
      </form>
    </div></div>
  )
}
