import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import { useToast } from '../../components/Toast'

/** US06 — Supprimer son compte. */
export default function DeleteAccountPage() {
  const { deleteAccount } = useAuth()
  const notify = useToast()
  const navigate = useNavigate()
  const [confirm, setConfirm] = useState(false)

  async function onDelete() {
    try {
      await deleteAccount()
    } catch {
      notify('La suppression a échoué. Réessayez.', 'error')
      return
    }
    navigate('/', { replace: true })
    notify('Votre compte a été supprimé.')
  }

  return (
    <div className="wrap page"><div className="narrow">
      <h1>Supprimer mon compte</h1>
      <div className="card">
        <p>Cette action est définitive :</p>
        <ul className="muted">
          <li>vos informations personnelles (nom, email, téléphone, photo) sont effacées ;</li>
          <li>vous ne pourrez plus vous connecter ;</li>
          <li>l'historique de vos locations et vos avis restent visibles, de façon anonyme.</li>
        </ul>
        <label className="check"><input type="checkbox" checked={confirm} onChange={(e) => setConfirm(e.target.checked)} /> Je comprends que cette action est définitive.</label>
        <div className="row between" style={{ marginTop: 16 }}>
          <Link className="muted" to="/profil">Garder mon compte</Link>
          <button className="btn danger" disabled={!confirm} onClick={onDelete}>Supprimer définitivement</button>
        </div>
      </div>
    </div></div>
  )
}
