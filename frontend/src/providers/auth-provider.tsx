'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { AuthResponse, SessionContextType } from '../types/auth';
import { User } from '../types/user';
import { setAccessToken, apiClient, internalClient } from '../lib/axios';

const AuthContext = createContext<SessionContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const router = useRouter();

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // Attempt to refresh token on initial load if we don't have user in state
        const { data } = await internalClient.post<{ access_token: string }>('/auth/refresh');
        setAccessToken(data.access_token);
        
        // Fetch current user details
        const userRes = await apiClient.get<User>('/users/me');
        setUser(userRes.data);
        setIsAuthenticated(true);
      } catch {
        // No valid session
        setAccessToken(null);
        setUser(null);
        setIsAuthenticated(false);
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();

    const handleUnauthorized = () => {
      setUser(null);
      setIsAuthenticated(false);
      router.push('/login');
    };

    const handleForbidden = () => {
      router.push('/403');
    };

    window.addEventListener('auth:unauthorized', handleUnauthorized);
    window.addEventListener('auth:forbidden', handleForbidden);
    return () => {
      window.removeEventListener('auth:unauthorized', handleUnauthorized);
      window.removeEventListener('auth:forbidden', handleForbidden);
    };
  }, [router]);

  const login = (data: AuthResponse) => {
    setAccessToken(data.tokens.access_token);
    setUser(data.user);
    setIsAuthenticated(true);
    if (data.user.role === 'ADMIN') {
      router.push('/admin');
    } else {
      router.push('/dashboard');
    }
  };

  const logout = async () => {
    try {
      await internalClient.post('/auth/logout');
    } finally {
      setAccessToken(null);
      setUser(null);
      setIsAuthenticated(false);
      router.push('/login');
    }
  };

  const updateUser = (updatedUser: User) => {
    setUser(updatedUser);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, isLoading, login, logout, updateUser }}>
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
