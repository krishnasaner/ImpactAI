import { useEffect, useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Heart, Mail, Lock, User, Shield, GraduationCap } from 'lucide-react';
import { LoginCredentials } from '@/types/auth';
import PageTransition from '@/components/ui/PageTransition';
import ScrollFadeIn from '@/components/ui/ScrollFadeIn';
import { FaGoogle } from 'react-icons/fa';
import { toast } from '@/components/ui/sonner';
import axios from 'axios';
import { useAuth } from '@/contexts/AuthContext';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleEnabled, setIsGoogleEnabled] = useState(false);
  const [isCheckingGoogleAuth, setIsCheckingGoogleAuth] = useState(true);

  const [credentials, setCredentials] = useState<LoginCredentials>({
    email: '',
    password: '',
    role: 'student',
  });

  const getDashboardRoute = (role: string) =>
    role === 'admin' || role === 'counselor' ? '/app/admin-dashboard' : '/app/student-dashboard';

  const handleLoginSuccess = (user: {
    id?: string;
    name: string;
    email?: string;
    role: 'student' | 'counselor' | 'admin';
    token: string;
  }) => {
    localStorage.setItem('userName', user.name);
    localStorage.setItem('userEmail', user.email || '');
    localStorage.setItem('userRole', user.role);
    localStorage.setItem('token', user.token);

    login({
      id: user.id || 'current-user',
      name: user.name,
      email: user.email || '',
      role: user.role,
    });
  };

  useEffect(() => {
    const checkGoogleAuthAvailability = async () => {
      try {
        const API_BASE_URL =
          import.meta.env.VITE_API_URL || `http://${window.location.hostname}:5000`;
        const response = await axios.get(`${API_BASE_URL}/auth/google/status`);
        setIsGoogleEnabled(Boolean(response.data?.configured));
      } catch {
        setIsGoogleEnabled(false);
      } finally {
        setIsCheckingGoogleAuth(false);
      }
    };

    void checkGoogleAuthAvailability();
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const id = params.get('id');
    const name = params.get('name');
    const email = params.get('email');
    const role = params.get('role');
    const token = params.get('token');
    const error = params.get('error');

    if (error) {
      toast.error(error);
      return;
    }

    if (name && role && token) {
      handleLoginSuccess({
        id: id || undefined,
        name,
        email: email || '',
        role: role as 'student' | 'counselor' | 'admin',
        token,
      });
      toast.success(`Welcome back, ${name}!`);
      navigate(getDashboardRoute(role), { replace: true });
    }
  }, [location, navigate]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const API_BASE_URL =
        import.meta.env.VITE_API_URL || `http://${window.location.hostname}:5000`;
      const res = await axios.post(`${API_BASE_URL}/auth/login`, credentials, {
        withCredentials: true,
      });
      const user = res.data.user;

      if (!user) {
        toast.error('Login failed. Please check your credentials.');
        return;
      }

      handleLoginSuccess({
        id: String(user.id),
        name: user.name,
        email: user.email,
        role: user.role,
        token: res.data.token,
      });

      toast.success('Logged in successfully!');
      navigate(getDashboardRoute(user.role));
    } catch (error) {
      console.error(error);
      toast.error('Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRoleChange = (role: 'student' | 'counselor' | 'admin') => {
    const demoCredentials = {
      student: { email: 'student@impactai.com', password: 'student123' },
      counselor: { email: 'counselor@impactai.com', password: 'counselor123' },
      admin: { email: 'admin@impactai.com', password: 'admin123' },
    };
    setCredentials({ ...demoCredentials[role], role });
  };

  const handleGoogleLogin = () => {
    if (!isGoogleEnabled) {
      toast.error(
        'Google sign-in is not configured yet. Please use email and password login for now.'
      );
      return;
    }

    const API_BASE_URL =
      import.meta.env.VITE_API_URL || `http://${window.location.hostname}:5000`;
    window.open(`${API_BASE_URL}/auth/google?role=${credentials.role}&next=login`, '_self');
  };

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'student':
        return <GraduationCap className="h-4 w-4" />;
      case 'counselor':
        return <Heart className="h-4 w-4" />;
      case 'admin':
        return <Shield className="h-4 w-4" />;
      default:
        return <User className="h-4 w-4" />;
    }
  };

  const getRoleDescription = (role: string) => {
    switch (role) {
      case 'student':
        return 'Access AI support, book sessions, and join peer forums';
      case 'counselor':
        return 'Manage sessions, provide support, and access resources';
      case 'admin':
        return 'View analytics, manage users, and oversee platform';
      default:
        return '';
    }
  };

  return (
    <PageTransition>
      <div className="flex flex-col bg-gradient-calm">
        <main className="min-h-screen flex items-center justify-center p-4">
          <div className="w-full max-w-md space-y-6">
            <ScrollFadeIn yOffset={20}>
              <div className="text-center space-y-2">
                <Link to="/" className="flex items-center justify-center space-x-2 group">
                  <img
                    src="/ImpactAI_logo.png"
                    alt="Impact AI Logo"
                    className="h-20 md:h-28 w-auto mx-auto object-contain"
                  />
                </Link>
                <p className="text-muted-foreground">Your trusted mental health companion</p>
              </div>
            </ScrollFadeIn>

            <ScrollFadeIn yOffset={16} delay={0.07}>
              <Card className="shadow-trust">
                <CardHeader className="space-y-1">
                  <CardTitle className="text-2xl text-center">Welcome Back</CardTitle>
                  <CardDescription className="text-center">
                    Choose your role to access your personalized dashboard
                  </CardDescription>
                </CardHeader>

                <CardContent>
                  <Tabs defaultValue="student" className="w-full">
                    <TabsList className="grid w-full grid-cols-3 mb-6">
                      {(['student', 'counselor', 'admin'] as const).map((role) => (
                        <TabsTrigger
                          key={role}
                          value={role}
                          onClick={() => handleRoleChange(role)}
                          className="flex items-center space-x-1"
                        >
                          {getRoleIcon(role)}
                          <span className="hidden sm:inline capitalize">{role}</span>
                        </TabsTrigger>
                      ))}
                    </TabsList>

                    {(['student', 'counselor', 'admin'] as const).map((role) => (
                      <TabsContent key={role} value={role} className="space-y-4">
                        <div className="text-center p-3 bg-muted rounded-lg">
                          <div className="flex items-center justify-center space-x-2 mb-1">
                            {getRoleIcon(role)}
                            <span className="font-medium capitalize">{role} Portal</span>
                          </div>
                          <p className="text-sm text-muted-foreground">
                            {getRoleDescription(role)}
                          </p>
                        </div>
                      </TabsContent>
                    ))}
                  </Tabs>

                  <form onSubmit={handleLogin} className="space-y-4 mt-6">
                    <div className="space-y-2">
                      <Label htmlFor="email">Email</Label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="email"
                          type="email"
                          placeholder="Enter your email"
                          value={credentials.email}
                          onChange={(e) =>
                            setCredentials({ ...credentials, email: e.target.value })
                          }
                          className="pl-10"
                          required
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="password">Password</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="password"
                          type="password"
                          placeholder="Enter your password"
                          value={credentials.password}
                          onChange={(e) =>
                            setCredentials({ ...credentials, password: e.target.value })
                          }
                          className="pl-10"
                          required
                        />
                      </div>
                    </div>

                    <Button
                      type="submit"
                      variant="hero"
                      size="lg"
                      className="w-full"
                      disabled={isLoading}
                    >
                      {isLoading ? 'Signing In...' : 'Sign In'}
                    </Button>
                  </form>

                  <Button
                    onClick={handleGoogleLogin}
                    variant="outline"
                    size="lg"
                    className="w-full mt-4 flex items-center justify-center space-x-2"
                    disabled={isCheckingGoogleAuth}
                  >
                    <FaGoogle className="h-5 w-5" />
                    <span>
                      {isCheckingGoogleAuth
                        ? 'Checking Google Sign-In...'
                        : 'Sign in with Google'}
                    </span>
                  </Button>

                  <div className="mt-6 text-center text-sm">
                    <span className="text-muted-foreground">Don’t have an account? </span>
                    <Link to="/signup" className="text-primary hover:underline font-medium">
                      Sign up
                    </Link>
                  </div>
                </CardContent>
              </Card>
            </ScrollFadeIn>

            <ScrollFadeIn delay={0.11}>
              <div className="text-center space-y-2 text-sm md:text-base text-muted-foreground">
                <p>Your privacy is protected with end-to-end encryption</p>
                <p>Confidential support available 24/7</p>
                <p>HIPAA compliant and stigma-free environment</p>
              </div>
            </ScrollFadeIn>
          </div>
        </main>
      </div>
    </PageTransition>
  );
};

export default Login;
