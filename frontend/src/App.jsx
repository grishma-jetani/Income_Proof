import { Routes, Route, Navigate } from 'react-router-dom'
import AppLayout from './layouts/AppLayout'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import UploadPage from './pages/UploadPage'
import ProcessingPage from './pages/ProcessingPage'
import TransactionsPage from './pages/TransactionsPage'
import ReportPage from './pages/ReportPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<LoginPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/processing" element={<ProcessingPage />} />
          <Route path="/transactions" element={<TransactionsPage />} />
          <Route path="/report" element={<ReportPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App