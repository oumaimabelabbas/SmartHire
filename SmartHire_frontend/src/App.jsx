import { Navigate, Route, Routes } from 'react-router-dom'
import Navbar from './components/Navbar'
import HomePage from './components/HomePage'
import AuthPage from './components/AuthPage'
import CandidatDashboardPage from './pages/candidat/Dashboard'
import OfferDetailsPage from './pages/candidat/OfferDetails'
import RecruiterDashboardPage from './pages/recruteur/Dashboard'
import RecruiterOfferDetailsPage from './pages/recruteur/OfferDetails'
import ProfilePage from './pages/Profile'
import './App.css'

function AppLayout() {
  return (
    <div className="app-shell">
      <div className="ambient ambient-a" aria-hidden="true" />
      <div className="ambient ambient-b" aria-hidden="true" />
      <Navbar />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/auth" element={<AuthPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/candidat/dashboard" element={<CandidatDashboardPage />} />
        <Route path="/candidat/offres/:offerId" element={<OfferDetailsPage />} />
        <Route path="/recruteur/dashboard" element={<RecruiterDashboardPage />} />
        <Route path="/recruteur/offres/:offerId" element={<RecruiterOfferDetailsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  )
}

export default AppLayout
