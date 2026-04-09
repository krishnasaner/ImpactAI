import React, { createContext, useContext, useMemo, useState, ReactNode } from 'react';
import type { User } from '@/types/auth';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
}

interface AuthContextType extends AuthState {
  login: (userData: User | null) => void;
  updateUser: (userData: Partial<User>) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const AUTH_USER_STORAGE_KEY = 'impactai_auth_user';

const getStoredUser = (): User | null => {
  if (typeof window === 'undefined') {
    return null;
  }

  try {
    const storedUser = localStorage.getItem(AUTH_USER_STORAGE_KEY);
    if (storedUser) {
      return JSON.parse(storedUser) as User;
    }

    const name = localStorage.getItem('userName');
    const email = localStorage.getItem('userEmail') || '';
    const role = localStorage.getItem('userRole') as User['role'] | null;
    const token = localStorage.getItem('token');

    if (name && role && token) {
      return {
        id: 'local-session',
        name,
        email,
        role,
      };
    }
  } catch (error) {
    console.error('Failed to restore auth state from storage:', error);
  }

  return null;
};

const persistUser = (user: User | null) => {
  if (typeof window === 'undefined') {
    return;
  }

  if (!user) {
    localStorage.removeItem(AUTH_USER_STORAGE_KEY);
    localStorage.removeItem('userName');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('userRole');
    return;
  }

  localStorage.setItem(AUTH_USER_STORAGE_KEY, JSON.stringify(user));
  localStorage.setItem('userName', user.name);
  localStorage.setItem('userEmail', user.email);
  localStorage.setItem('userRole', user.role);
};

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>(() => {
    const storedUser = getStoredUser();
    return {
      user: storedUser,
      isAuthenticated: Boolean(storedUser && localStorage.getItem('token')),
    };
  });

  const login = (userData: User | null) => {
    if (!userData) {
      return;
    }

    persistUser(userData);
    setAuthState({
      user: userData,
      isAuthenticated: true,
    });
  };

  const updateUser = (userData: Partial<User>) => {
    setAuthState((currentState) => {
      if (!currentState.user) {
        return currentState;
      }

      const updatedUser = { ...currentState.user, ...userData };
      persistUser(updatedUser);

      return {
        ...currentState,
        user: updatedUser,
      };
    });
  };

  const logout = () => {
    persistUser(null);
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
    }

    setAuthState({
      user: null,
      isAuthenticated: false,
    });
  };

  const value = useMemo(
    () => ({ ...authState, login, updateUser, logout }),
    [authState]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
