import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import HomePage from './pages/HomePage'
import DeleteAccountPage from './pages/users/DeleteAccountPage'
import EditProfilePage from './pages/users/EditProfilePage'
import LoginPage from './pages/users/LoginPage'
import MembersPage from './pages/users/MembersPage'
import ProfilePage from './pages/users/ProfilePage'
import PublicProfilePage from './pages/users/PublicProfilePage'
import RegisterPage from './pages/users/RegisterPage'
import MessagesPage from './pages/messaging/MessagesPage'

const privatePage = (page) => <ProtectedRoute>{page}</ProtectedRoute>

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<HomePage />} />

        {/* Module « Gestion des utilisateurs » */}
        <Route path="connexion" element={<LoginPage />} />
        <Route path="inscription" element={<RegisterPage />} />
        <Route path="profil" element={privatePage(<ProfilePage />)} />
        <Route path="profil/modifier" element={privatePage(<EditProfilePage />)} />
        <Route path="profil/supprimer" element={privatePage(<DeleteAccountPage />)} />
        <Route path="membres" element={<MembersPage />} />
        <Route path="membres/:id" element={<PublicProfilePage />} />
        {/* Module « Messagerie » */}
        <Route path="messages" element={privatePage(<MessagesPage />)} />
        <Route path="messages/:id" element={privatePage(<MessagesPage />)} />

        {/* Les autres modules ajoutent leurs routes ici (annonces, réservations, avis, messagerie). */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
