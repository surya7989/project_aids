import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { Layout } from '@/components/layout/Layout'
import Login from '@/pages/Login'
import Dashboard from '@/pages/Dashboard'
import Packets from '@/pages/Packets'
import Threats from '@/pages/Threats'
import Alerts from '@/pages/Alerts'
import Analytics from '@/pages/Analytics'
import ML from '@/pages/ML'
import Users from '@/pages/Users'
import Settings from '@/pages/Settings'
import Logs from '@/pages/Logs'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  return (
    <Routes>
      <Route path="/login" element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />} />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/packets" element={<Packets />} />
        <Route path="/flows" element={<Packets />} />
        <Route path="/threats" element={<Threats />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/ml" element={<ML />} />
        <Route path="/users" element={<Users />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/logs" element={<Logs />} />
      </Route>
      <Route path="*" element={<Navigate to={isAuthenticated ? '/dashboard' : '/login'} replace />} />
    </Routes>
  )
}
