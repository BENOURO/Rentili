import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import AuthAside from '../../components/AuthAside'
import Field from '../../components/Field'
import { useToast } from '../../components/Toast'

/** US01 — S'inscrire. */
export default function RegisterPage() {
  const { register } = useAuth()
  const notify = useToast()
  const navigate = useNavigate()
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', city: '', password: '', password2: '' })
  const [errors, setErrors] = useState({})
  const [busy, setBusy] = useState(false)
  const set = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  async function onSubmit(e) {
    e.preventDefault()
    if (form.password !== form.password2) { setErrors({ password2: ['Les deux mots de passe ne correspondent pas.'] }); return }
    setBusy(true); setErrors({})
    try {
      const { first_name, last_name, email, city, password } = form
      await register({ first_name, last_name, email, city, password })
      notify('Compte créé. Bienvenue sur RENTILI !')
      navigate('/profil')
    } catch (err) {
      setErrors(err.fields)
    } finally { setBusy(false) }
  }

  return (
    <div className="auth">
      <AuthAside />
      <div className="auth-main"><div className="box">
        <h1>Créer un compte</h1>
        <p className="muted">Déjà inscrit ? <Link to="/connexion">Connectez-vous</Link>.</p>
        <form onSubmit={onSubmit} noValidate>
          {errors.non_field_errors && <div className="alert">{errors.non_field_errors.join(' ')}</div>}
          <div className="grid-2">
            <Field label="Prénom" name="first_name" value={form.first_name} onChange={set} errors={errors} required />
            <Field label="Nom" name="last_name" value={form.last_name} onChange={set} errors={errors} required />
          </div>
          <Field label="Email" name="email" type="email" value={form.email} onChange={set} errors={errors} required />
          <Field label="Ville" name="city" value={form.city} onChange={set} errors={errors} />
          <Field label="Mot de passe" name="password" type="password" value={form.password} onChange={set} errors={errors} required
            help="8 caractères minimum, pas uniquement des chiffres, pas un mot de passe courant." />
          <Field label="Confirmer le mot de passe" name="password2" type="password" value={form.password2} onChange={set} errors={errors} required />
          <button className="btn block" disabled={busy}>{busy ? 'Création…' : 'Créer mon compte'}</button>
          <p className="small muted" style={{ marginTop: 12 }}>Un même compte permet de louer et de proposer des objets.</p>
        </form>
      </div></div>
    </div>
  )
}
