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
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<{ role: string } | null>(authUser ? { role: authUser.role } : null);
  const hasChecked = useRef(false);

  useEffect(() => {
    if (authUser?.isAnonymous) {
      setUser({ role: authUser.role });
      setLoading(false);
      hasChecked.current = true;
      return;
    }

    if (hasChecked.current) {
      setUser(authUser ? { role: authUser.role } : null);
      setLoading(false);
      return;
    }

    const checkAuth = async () => {
      try {
        const res = await api.get('/auth/me');
        const currentUser = res.data?.user || res.data?.data?.user;
        if (res.data?.success && currentUser) {
          setUser(currentUser);
          login(
            {
              id: String(currentUser.id),
              name: currentUser.name || currentUser.email,
              email: currentUser.email || '',
              role: currentUser.role,
            },
            { remember: true }
          );
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
