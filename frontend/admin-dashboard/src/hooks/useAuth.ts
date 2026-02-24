import { useState, useCallback, useEffect } from 'react';
import { AuthState, LoginRequest, LoginResponse } from '../types/index';
import api from '../services/api';

export const useAuth = () => {
  const [auth, setAuth] = useState<AuthState>({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: true,
  });

  // Initialize auth state from localStorage
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const userJson = localStorage.getItem('user');

    if (token && userJson) {
      try {
        const user = JSON.parse(userJson);
        setAuth({
          user,
          token,
          isAuthenticated: true,
          isLoading: false,
        });
      } catch (error) {
        console.error('Failed to parse stored user:', error);
        localStorage.removeItem('user');
        localStorage.removeItem('access_token');
        setAuth({ user: null, token: null, isAuthenticated: false, isLoading: false });
      }
    } else {
      setAuth({ user: null, token: null, isAuthenticated: false, isLoading: false });
    }
  }, []);

  const login = useCallback(async (credentials: LoginRequest) => {
    try {
      setAuth((prev) => ({ ...prev, isLoading: true }));
      const response: LoginResponse = await api.login(credentials);

      setAuth({
        user: response.user,
        token: response.access_token,
        isAuthenticated: true,
        isLoading: false,
      });

      return response;
    } catch (error) {
      setAuth({ user: null, token: null, isAuthenticated: false, isLoading: false });
      throw error;
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      setAuth((prev) => ({ ...prev, isLoading: true }));
      await api.logout();
    } finally {
      setAuth({ user: null, token: null, isAuthenticated: false, isLoading: false });
    }
  }, []);

  const refreshAuth = useCallback(async () => {
    // Verify token is still valid
    try {
      const userJson = localStorage.getItem('user');
      const token = localStorage.getItem('access_token');

      if (!userJson || !token) {
        setAuth({ user: null, token: null, isAuthenticated: false, isLoading: false });
        return;
      }

      const user = JSON.parse(userJson);
      setAuth({
        user,
        token,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error) {
      console.error('Failed to refresh auth:', error);
      setAuth({ user: null, token: null, isAuthenticated: false, isLoading: false });
    }
  }, []);

  return {
    auth,
    login,
    logout,
    refreshAuth,
  };
};
