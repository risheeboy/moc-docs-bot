import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';

// Pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics';
import Documents from './pages/Documents';
import ScrapeJobs from './pages/ScrapeJobs';
import Conversations from './pages/Conversations';
import Feedback from './pages/Feedback';
import SystemConfig from './pages/SystemConfig';
import ModelMonitoring from './pages/ModelMonitoring';
import AuditLog from './pages/AuditLog';

// Styles
import './styles/globals.css';

const App: React.FC = () => {
  const { auth, login, logout, refreshAuth } = useAuth();
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    refreshAuth();
    setIsInitialized(true);
  }, [refreshAuth]);

  if (!isInitialized) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <Router>
      <Routes>
        <Route
          path="/login"
          element={
            auth.isAuthenticated ? (
              <Navigate to="/dashboard" replace />
            ) : (
              <Login onLoginSuccess={() => {}} />
            )
          }
        />

        <Route
          path="/*"
          element={
            <ProtectedRoute auth={auth} requiredRole={['admin']}>
              <Layout auth={auth} onLogout={logout}>
                <Routes>
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/analytics" element={<Analytics />} />
                  <Route path="/documents" element={<Documents />} />
                  <Route path="/scrape-jobs" element={<ScrapeJobs />} />
                  <Route path="/conversations" element={<Conversations />} />
                  <Route path="/feedback" element={<Feedback />} />
                  <Route path="/system-config" element={<SystemConfig />} />
                  <Route path="/model-monitoring" element={<ModelMonitoring />} />
                  <Route path="/audit-log" element={<AuditLog />} />
                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                </Routes>
              </Layout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  );
};

export default App;
