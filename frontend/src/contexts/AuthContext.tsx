import React, { createContext, useCallback, useContext, useMemo, useState, useEffect, ReactNode } from 'react';
import type { User } from '@/types/auth';
import api from '@/services/api';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
}

interface LoginOptions {
  remember?: boolean;
  anonymous?: boolean;
}

interface AuthContextType extends AuthState {
  login: (userData: User | null, options?: LoginOptions) => void;
  updateUser: (userData: Partial<User>) => void;
  logout: () => void;
}

type SessionPersistence = 'local' | 'session';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const AUTH_USER_STORAGE_KEY = 'impactai_auth_user';

const getStorage = (persistence: SessionPersistence) =>
  persistence === 'session' ? window.sessionStorage : window.localStorage;

const clearLegacyStorage = () => {
  window.localStorage.removeItem('token');
  window.localStorage.removeItem('userName');
  window.localStorage.removeItem('userEmail');
  window.localStorage.removeItem('userRole');
  window.sessionStorage.removeItem('token');
  window.sessionStorage.removeItem('userName');
  window.sessionStorage.removeItem('userEmail');
  window.sessionStorage.removeItem('userRole');
};

const clearStoredAuth = () => {
  if (typeof window === 'undefined') {
    return;
  }

  [window.localStorage, window.sessionStorage].forEach((storage) => {
    storage.removeItem(AUTH_USER_STORAGE_KEY);
  });

  clearLegacyStorage();
};

const persistSession = (
  user: User | null,
  persistence: SessionPersistence = 'local'
) => {
  if (typeof window === 'undefined') {
    return;
  }

  clearStoredAuth();

  if (!user) {
    return;
  }

  const storage = getStorage(persistence);
  storage.setItem(AUTH_USER_STORAGE_KEY, JSON.stringify(user));
  storage.setItem('userName', user.name);
  storage.setItem('userEmail', user.email || '');
  storage.setItem('userRole', user.role);
};

const getStoredAuth = (): { user: User | null; persistence: SessionPersistence } => {
  if (typeof window === 'undefined') {
    return { user: null, persistence: 'local' };
  }

  for (const persistence of ['session', 'local'] as const) {
    const storage = getStorage(persistence);

    try {
      const storedUser = storage.getItem(AUTH_USER_STORAGE_KEY);

      if (storedUser) {
        return {
          user: JSON.parse(storedUser) as User,
          persistence,
        };
      }
    } catch (error) {
      console.error('Failed to restore auth state from storage:', error);
    }
  }

  try {
    const name = window.localStorage.getItem('userName') || window.sessionStorage.getItem('userName');
    const email =
      window.localStorage.getItem('userEmail') || window.sessionStorage.getItem('userEmail') || '';
    const role =
      (window.localStorage.getItem('userRole') ||
        window.sessionStorage.getItem('userRole')) as User['role'] | null;

    if (name && role) {
      return {
        user: {
          id: 'local-session',
          name,
          email,
          role,
        },
        persistence: 'local',
      };
    }
  } catch (error) {
    console.error('Failed to restore auth state from legacy storage:', error);
  }

  return { user: null, persistence: 'local' };
};

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>(() => {
    const { user } = getStoredAuth();
    return {
      user,
      isAuthenticated: Boolean(user && user.isAnonymous),
    };
  });

  const logout = useCallback(() => {
    clearStoredAuth();
    setAuthState({
      user: null,
      isAuthenticated: false,
    });
    // Fire API call to clear backend cookies
    api.post('/auth/logout').catch(() => {});
  }, []);

  const login = useCallback((userData: User | null, options?: LoginOptions) => {
    if (!userData) {
      return;
    }

    const nextUser = options?.anonymous ? { ...userData, isAnonymous: true } : userData;
    persistSession(nextUser, options?.remember === false ? 'session' : 'local');

    setAuthState({
      user: nextUser,
      isAuthenticated: true,
    });
  }, []);

  const updateUser = useCallback((userData: Partial<User>) => {
    setAuthState((currentState) => {
      if (!currentState.user) {
        return currentState;
      }

      const stored = getStoredAuth();
      const updatedUser = { ...currentState.user, ...userData };
      persistSession(updatedUser, stored.persistence);

      return {
        ...currentState,
        user: updatedUser,
      };
    });
  }, []);

  // Silent session restoration and global logout listener
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const res = await api.get('/auth/me');
        if (res.data.success && res.data.user) {
          login(res.data.user, { remember: true });
        }
      } catch (err) {
        clearStoredAuth();
        setAuthState({
          user: null,
          isAuthenticated: false,
        });
      }
    };

    const handleGlobalLogout = () => {
      clearStoredAuth();
      setAuthState({
        user: null,
        isAuthenticated: false,
      });
    };

    window.addEventListener('auth-logout', handleGlobalLogout);
    void initializeAuth();

    return () => {
      window.removeEventListener('auth-logout', handleGlobalLogout);
    };
  }, [login]);

  const value = useMemo(
    () => ({ ...authState, login, updateUser, logout }),
    [authState, login, updateUser, logout]
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
