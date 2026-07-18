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
import api from '@/services/api';

interface SignupCredentials {
  email: string;
  password: string;
  confirmPassword: string;
  role: 'student' | 'counselor' | 'admin';
}

const Signup = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated, user: authUser } = useAuth();
  const [credentials, setCredentials] = useState<SignupCredentials>({
    email: '',
    password: '',
    confirmPassword: '',
    role: 'student',
  });
  const [loading, setLoading] = useState(false);
  const [isGoogleEnabled, setIsGoogleEnabled] = useState(false);
  const [isCheckingGoogleAuth, setIsCheckingGoogleAuth] = useState(true);
  const [rememberMe, setRememberMe] = useState(true);

  const getDashboardRoute = (role: string) =>
    role === 'admin' || role === 'counselor' ? '/app/admin-dashboard' : '/app/student-dashboard';

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && authUser) {
      navigate(getDashboardRoute(authUser.role), { replace: true });
    }
  }, [isAuthenticated, authUser, navigate]);

  useEffect(() => {
    const checkGoogleAuthAvailability = async () => {
      try {
        const res = await api.get('/auth/google/status');
        setIsGoogleEnabled(Boolean(res.data?.configured));
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
    const error = params.get('error');

    if (error) {
      toast.error(error);
    }
  }, [location]);

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

  const validatePasswordPolicy = (pwd: string): boolean => {
    const common = ["123", "password", "123456", "qwerty", "abc123"];
    if (common.includes(pwd.toLowerCase())) {
      toast.error('Password is too common and weak.');
      return false;
    }
    if (pwd.length < 12) {
      toast.error('Password must be at least 12 characters long.');
      return false;
    }
    if (!/[A-Z]/.test(pwd)) {
      toast.error('Password must contain at least one uppercase letter.');
      return false;
    }
    if (!/[a-z]/.test(pwd)) {
      toast.error('Password must contain at least one lowercase letter.');
      return false;
    }
    if (!/\d/.test(pwd)) {
      toast.error('Password must contain at least one number.');
      return false;
    }
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(pwd)) {
      toast.error('Password must contain at least one special character.');
      return false;
    }
    return true;
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    if (credentials.password !== credentials.confirmPassword) {
      toast.error('Passwords do not match.');
      setLoading(false);
      return;
    }

    if (!validatePasswordPolicy(credentials.password)) {
      setLoading(false);
      return;
    }

    try {
      const res = await api.post('/auth/signup', {
        email: credentials.email,
        password: credentials.password,
        confirm_password: credentials.confirmPassword,
        role: credentials.role,
        remember_me: rememberMe,
      });

      const user = res.data?.user || res.data?.data?.user;

      login({
        id: String(user.id),
        name: user.name || user.email,
        email: user.email || credentials.email,
        role: user.role,
      }, { remember: rememberMe });

      toast.success('Account created successfully!');
      navigate(getDashboardRoute(user.role));
    } catch (err: any) {
      console.error(err);
      const errMsg = err.response?.data?.detail || 'Signup failed. Please check your credentials.';
      toast.error(errMsg);
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

                    <div className="space-y-2">
                      <Label htmlFor="confirmPassword">Confirm Password</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="confirmPassword"
                          type="password"
                          placeholder="Confirm your password"
                          value={credentials.confirmPassword || ''}
                          onChange={(e) =>
                            setCredentials({ ...credentials, confirmPassword: e.target.value })
                          }
                          className="pl-10"
                          required
                        />
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id="rememberMe"
                        checked={rememberMe}
                        onChange={(e) => setRememberMe(e.target.checked)}
                        className="h-4 w-4 rounded border-gray-300 text-teal-600 focus:ring-teal-500 bg-[#071A1F]"
                      />
                      <Label htmlFor="rememberMe" className="text-sm text-muted-foreground cursor-pointer">
                        Remember Me
                      </Label>
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
