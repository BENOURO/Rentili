import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import AuthAside from '../../components/AuthAside'
import Field from '../../components/Field'
import { useToast } from '../../components/Toast'

/** US02 — Se connecter. */
export default function LoginPage() {
  const { login } = useAuth()
  const notify = useToast()
  const navigate = useNavigate()
  const from = useLocation().state?.from || '/'
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function onSubmit(e) {
    e.preventDefault()
    setBusy(true); setError('')
    try {
      const user = await login(form.email, form.password)
      notify(`Bienvenue, ${user.first_name} !`)
      navigate(from, { replace: true })
    } catch (err) {
      setError(err.message)
    } finally { setBusy(false) }
  }
  const set = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  return (
    <div className="auth">
      <AuthAside />
      <div className="auth-main"><div className="box">
        <h1>Bon retour</h1>
        <p className="muted">Pas encore de compte ? <Link to="/inscription">Inscrivez-vous</Link>.</p>
        <form onSubmit={onSubmit}>
          {error && <div className="alert">{error}</div>}
          <Field label="Email" name="email" type="email" value={form.email} onChange={set} required autoFocus />
          <Field label="Mot de passe" name="password" type="password" value={form.password} onChange={set} required />
          <button className="btn block" disabled={busy}>{busy ? 'Connexion…' : 'Se connecter'}</button>
        </form>
        <div className="demo-accounts"><b>Comptes de démonstration</b> — mot de passe <code>rentili2026</code><br />
          <code>yasmine@rentili.tn</code> · <code>karim@rentili.tn</code> · admin : <code>admin@rentili.tn</code></div>
      </div></div>
    </div>
  )
}
