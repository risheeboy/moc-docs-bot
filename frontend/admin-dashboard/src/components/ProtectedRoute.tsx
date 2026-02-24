import React from 'react';
import { Navigate } from 'react-router-dom';
import { AuthState } from '../types/index';

interface ProtectedRouteProps {
  children: React.ReactNode;
  auth: AuthState;
  requiredRole?: string[];
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  auth,
  requiredRole,
}) => {
  if (auth.isLoading) {
    return (
      <div className="flex-center" style={{ height: '100vh' }}>
        <div className="spinner"></div>
      </div>
    );
  }

  if (!auth.isAuthenticated || !auth.user) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole && !requiredRole.includes(auth.user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
