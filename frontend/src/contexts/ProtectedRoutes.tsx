import { useEffect, useRef, useState, ReactNode } from 'react';
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
  // Prevent re-running the auth check when login/logout references change
  const hasChecked = useRef(false);

  useEffect(() => {
    // Skip if we already verified this session
    if (hasChecked.current) return;

    const checkAuth = async () => {
      const token = sessionStorage.getItem('token') || localStorage.getItem('token');

      if (authUser?.isAnonymous) {
        setUser({ role: authUser.role });
        setLoading(false);
        hasChecked.current = true;
        return;
      }

      // If AuthContext already has a valid user (e.g. just logged in),
      // trust it and skip the redundant /me round-trip.
      if (authUser && token) {
        setUser({ role: authUser.role });
        setLoading(false);
        hasChecked.current = true;
        return;
      }

      if (!token) {
        setUser(null);
        setLoading(false);
        hasChecked.current = true;
        return;
      }

      // Token exists but no user in context (page refresh) — verify via /me
      try {
        const API_BASE_URL =
          import.meta.env.VITE_API_URL || `http://${window.location.hostname}:5000`;
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 10000);
        const res = await axios.get(`${API_BASE_URL}/api/auth/me`, {
          withCredentials: true,
          headers: {
            Authorization: `Bearer ${token}`,
          },
          signal: controller.signal,
        });
        clearTimeout(timer);

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
        hasChecked.current = true;
      }
    };

    void checkAuth();
    // Only depend on authUser — login/logout are stable identity functions
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
