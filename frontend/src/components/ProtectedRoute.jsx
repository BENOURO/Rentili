import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

/** Réserve une page aux utilisateurs connectés ; sinon redirige vers la connexion puis revient ici. */
export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <div className="wrap page muted">Chargement…</div>
  if (!user) return <Navigate to="/connexion" replace state={{ from: location.pathname }} />
  return children
}
