import { Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Frameworks from './pages/Frameworks';
import ControlDetail from './pages/ControlDetail';
import EvidenceDetail from './pages/EvidenceDetail';
import RiskMatrix from './pages/RiskMatrix';
import Collectors from './pages/Collectors';
import Layout from './components/Layout';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('token');
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="frameworks" element={<Frameworks />} />
        <Route path="controls/:id" element={<ControlDetail />} />
        <Route path="evidence/:id" element={<EvidenceDetail />} />
        <Route path="risk" element={<RiskMatrix />} />
        <Route path="collectors" element={<Collectors />} />
      </Route>
    </Routes>
  );
}
