'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { apiClient, User, LoginRequest, RegisterRequest } from './api-client';

type AuthContextType = {
  user: User | null;
  token: string | null;
  login: (data: LoginRequest) => Promise<void>;
  logout: () => void;
  register: (data: RegisterRequest) => Promise<void>;
  isLoading: boolean;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = apiClient.getToken();
      if (storedToken) {
        setToken(storedToken);
        try {
          const userData = await apiClient.getMe();
          setUser(userData);
        } catch (error) {
          console.error('Failed to validate token:', error);
          apiClient.clearToken();
          setToken(null);
          setUser(null);
        }
      }
      setIsLoading(false);
    };
    initAuth();
  }, []);

  const login = useCallback(async (data: LoginRequest) => {
    const response = await apiClient.login(data);
    const accessToken = response.access_token;
    apiClient.setToken(accessToken);
    setToken(accessToken);
    const userData = await apiClient.getMe();
    setUser(userData);
  }, []);

  const register = useCallback(async (data: RegisterRequest) => {
    await apiClient.register(data);
  }, []);

  const logout = useCallback(() => {
    apiClient.clearToken();
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, login, logout, register, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
