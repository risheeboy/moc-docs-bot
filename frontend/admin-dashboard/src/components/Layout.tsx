import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { AuthState } from '../types/index';
import api from '../services/api';
import '../styles/Layout.css';

interface LayoutProps {
  children: React.ReactNode;
  auth: AuthState;
  onLogout: () => Promise<void>;
}

const Layout: React.FC<LayoutProps> = ({ children, auth, onLogout }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleLogout = async () => {
    try {
      await onLogout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const isActive = (path: string) => location.pathname === path;

  const menuItems = [
    { path: '/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/analytics', label: 'Analytics', icon: '📈' },
    { path: '/documents', label: 'Documents', icon: '📄' },
    { path: '/scrape-jobs', label: 'Scrape Jobs', icon: '🌐' },
    { path: '/conversations', label: 'Conversations', icon: '💬' },
    { path: '/feedback', label: 'Feedback', icon: '⭐' },
    { path: '/system-config', label: 'System Config', icon: '⚙️' },
    { path: '/model-monitoring', label: 'Model Monitoring', icon: '🤖' },
    { path: '/audit-log', label: 'Audit Log', icon: '📋' },
  ];

  return (
    <div className="layout">
      <header className="layout-header">
        <div className="header-content">
          <button
            className="sidebar-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            aria-label="Toggle sidebar"
          >
            ☰
          </button>
          <h1>Ministry of Culture - Admin Dashboard</h1>
          <div className="header-user">
            <div className="user-menu-trigger" onClick={() => setShowUserMenu(!showUserMenu)}>
              <span className="user-name">{auth.user?.username}</span>
              <span className="user-role">{auth.user?.role}</span>
            </div>
            {showUserMenu && (
              <div className="user-menu">
                <div className="user-info">
                  <strong>{auth.user?.username}</strong>
                  <p>{auth.user?.email}</p>
                </div>
                <button className="btn btn-danger btn-sm" onClick={handleLogout}>
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="layout-container">
        <aside className={`layout-sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
          <nav>
            <ul className="nav-menu">
              {menuItems.map((item) => (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`nav-link ${isActive(item.path) ? 'active' : ''}`}
                    onClick={() => {
                      // Close sidebar on mobile after navigation
                      if (window.innerWidth <= 768) {
                        setSidebarOpen(false);
                      }
                    }}
                  >
                    <span className="nav-icon">{item.icon}</span>
                    <span className="nav-label">{item.label}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </aside>

        <main className="layout-main">
          <div className="main-content">{children}</div>
        </main>
      </div>
    </div>
  );
};

export default Layout;
