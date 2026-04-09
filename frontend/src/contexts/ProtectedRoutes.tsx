import { useEffect, useState, ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '@/contexts/AuthContext';

interface ProtectedRouteProps {
  children: ReactNode;
  roles?: string[];
}

const ProtectedRoute = ({ children, roles }: ProtectedRouteProps) => {
  const { login, logout, user: authUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<{ role: string } | null>(null);

  useEffect(() => {
    const checkAuth = async () => {
      const token = sessionStorage.getItem('token') || localStorage.getItem('token');

      if (authUser?.isAnonymous) {
        setUser({ role: authUser.role });
        setLoading(false);
        return;
      }

      if (!token) {
        setUser(null);
        setLoading(false);
        return;
      }

      try {
        const API_BASE_URL =
          import.meta.env.VITE_API_URL || `http://${window.location.hostname}:5000`;
        const res = await axios.get(`${API_BASE_URL}/api/auth/me`, {
          withCredentials: true,
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        setUser(res.data.user);
        login({
          id: String(res.data.user.id),
          name: res.data.user.name,
          email: res.data.user.email,
          role: res.data.user.role,
        }, { token });
      } catch {
        sessionStorage.removeItem('token');
        localStorage.removeItem('token');
        logout();
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    void checkAuth();
  }, [authUser, login, logout]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
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
