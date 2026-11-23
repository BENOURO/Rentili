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
import AvisPage from './pages/AvisPage'
import AnnoncePage from './pages/reservations/AnnoncePage'
import AnnoncesPage from './pages/reservations/AnnoncesPage'
import MesReservationsPage from './pages/reservations/MesReservationsPage'
import AnnonceFormPage from './pages/reservations/AnnonceFormPage'
import './App.css'

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
        {/* Module « Gestion des avis » */}
        <Route path="avis" element={<AvisPage />} />
        {/* Modules « Gestion des annonces » et « Gestion des réservations » */}
        <Route path="annonces" element={<AnnoncesPage />} />
        <Route path="annonces/publier" element={privatePage(<AnnonceFormPage />)} />
        <Route path="annonces/:id/modifier" element={privatePage(<AnnonceFormPage mode="edit" />)} />
        <Route path="annonces/:id" element={<AnnoncePage />} />
        <Route path="reservations" element={privatePage(<MesReservationsPage />)} />

        {/* Les autres modules ajoutent leurs routes ici (annonces, réservations, avis, messagerie). */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
