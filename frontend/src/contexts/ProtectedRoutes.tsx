import { useEffect, useRef, useState, ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import api from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';

interface ProtectedRouteProps {
  children: ReactNode;
  roles?: string[];
}

const ProtectedRoute = ({ children, roles }: ProtectedRouteProps) => {
  const { login, logout, user: authUser } = useAuth();
  const [loading, setLoading] = useState(!authUser);
  const [user, setUser] = useState<{ role: string } | null>(authUser ? { role: authUser.role } : null);
  const hasChecked = useRef(false);

  useEffect(() => {
    if (authUser) {
      setUser({ role: authUser.role });
      setLoading(false);
      return;
    }

    if (hasChecked.current) return;

    const checkAuth = async () => {
      try {
        const res = await api.get('/auth/me');
        if (res.data.success && res.data.user) {
          setUser(res.data.user);
          login(res.data.user, { remember: true });
        } else {
          setUser(null);
          logout();
        }
      } catch {
        logout();
        setUser(null);
      } finally {
        setLoading(false);
        hasChecked.current = true;
      }
    };

    void checkAuth();
  }, [authUser, login, logout]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#071A1F] text-[#F8FAFC]">
        Checking authentication...
      </div>
    );
  }

  if (!user || (roles && !roles.includes(user.role))) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
