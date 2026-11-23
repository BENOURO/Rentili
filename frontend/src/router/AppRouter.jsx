import { Navigate, Route, Routes } from 'react-router-dom'
import AvisPage from '../pages/AvisPage'

export default function AppRouter() {
  return (
    <Routes>
      <Route path="/avis" element={<AvisPage />} />
      <Route path="/" element={<Navigate to="/avis" replace />} />
      <Route path="*" element={<Navigate to="/avis" replace />} />
    </Routes>
  )
}
