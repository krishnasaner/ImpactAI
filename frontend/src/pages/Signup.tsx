import { useEffect, useState } from 'react';
import { toast } from 'react-toastify';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Heart, Mail, Lock, User, Shield, GraduationCap } from 'lucide-react';
import PageTransition from '@/components/ui/PageTransition';
import ScrollFadeIn from '@/components/ui/ScrollFadeIn';
import { FaGoogle } from 'react-icons/fa';
import { useAuth } from '@/contexts/AuthContext';

interface SignupCredentials {
  email: string;
  password: string;
  role: 'student' | 'counselor' | 'admin';
}

const Signup = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [credentials, setCredentials] = useState<SignupCredentials>({
    email: '',
    password: '',
    role: 'student',
  });
  const [loading, setLoading] = useState(false);
  const [isGoogleEnabled, setIsGoogleEnabled] = useState(false);
  const [isCheckingGoogleAuth, setIsCheckingGoogleAuth] = useState(true);

  const getDashboardRoute = (role: string) =>
    role === 'admin' || role === 'counselor' ? '/app/admin-dashboard' : '/app/student-dashboard';

  useEffect(() => {
    const checkGoogleAuthAvailability = async () => {
      try {
        const API_BASE_URL =
          import.meta.env.VITE_API_URL || `http://${window.location.hostname}:5000`;
        const res = await fetch(`${API_BASE_URL}/auth/google/status`);
        const data = await res.json();
        setIsGoogleEnabled(Boolean(data?.configured));
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
      login({
        id: id || 'current-user',
        name,
        email: email || '',
        role: role as 'student' | 'counselor' | 'admin',
      }, { token });

      toast.success(`Welcome, ${name}!`);
      navigate(getDashboardRoute(role), { replace: true });
    }
  }, [location, login, navigate]);

  const handleRoleChange = (role: 'student' | 'counselor' | 'admin') => {
    setCredentials({ ...credentials, role });
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

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const API_BASE_URL =
        import.meta.env.VITE_API_URL || `http://${window.location.hostname}:5000`;
      const res = await fetch(`${API_BASE_URL}/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
        credentials: 'include',
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => null);
        throw new Error(errData?.detail || 'Signup failed');
      }

      const data = await res.json();
      const user = data.user;

      login({
        id: String(user.id),
        name: user.name || user.email,
        email: user.email || credentials.email,
        role: user.role,
      }, { token: data.token });

      toast.success('Account created successfully!');
      navigate(getDashboardRoute(user.role));
    } catch (err: any) {
      console.error(err);
      toast.error(err.message || 'Signup failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignup = () => {
    if (!isGoogleEnabled) {
      toast.error(
        'Google sign-up is not configured yet. Please use email and password signup for now.'
      );
      return;
    }

    const API_BASE_URL =
      import.meta.env.VITE_API_URL || `http://${window.location.hostname}:5000`;
    window.location.href = `${API_BASE_URL}/auth/google?role=${credentials.role}&next=signup`;
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
                  <CardTitle className="text-2xl text-center">Create Your Account</CardTitle>
                  <CardDescription className="text-center">
                    Choose your role to get started
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

                  <form onSubmit={handleSignup} className="space-y-4 mt-6">
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
                      disabled={loading}
                    >
                      {loading ? 'Signing Up...' : 'Sign Up'}
                    </Button>
                  </form>

                  <Button
                    onClick={handleGoogleSignup}
                    variant="outline"
                    size="lg"
                    className="w-full mt-4 flex items-center justify-center space-x-2"
                    disabled={isCheckingGoogleAuth}
                  >
                    <FaGoogle className="h-5 w-5" />
                    <span>
                      {isCheckingGoogleAuth
                        ? 'Checking Google Sign-Up...'
                        : 'Sign up with Google'}
                    </span>
                  </Button>

                  <div className="mt-6 text-center text-sm">
                    <span className="text-muted-foreground">Already have an account? </span>
                    <Link to="/login" className="text-primary hover:underline font-medium">
                      Log in
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

export default Signup;
