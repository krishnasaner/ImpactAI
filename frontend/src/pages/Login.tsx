import { useEffect, useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Heart, Mail, Lock, User, Shield, GraduationCap, Eye, EyeOff } from 'lucide-react';
import { LoginCredentials } from '@/types/auth';
import PageTransition from '@/components/ui/PageTransition';
import ScrollFadeIn from '@/components/ui/ScrollFadeIn';
import { FaGoogle } from 'react-icons/fa';
import { toast } from '@/components/ui/sonner';
import api from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated, user: authUser } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleEnabled, setIsGoogleEnabled] = useState(false);
  const [isCheckingGoogleAuth, setIsCheckingGoogleAuth] = useState(true);
  const [rememberMe, setRememberMe] = useState(true);
  const [showPassword, setShowPassword] = useState(false);

  const [credentials, setCredentials] = useState<LoginCredentials>({
    email: '',
    password: '',
    role: 'student',
  });

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
        // Short timeout — don't block the login page waiting for a cold-starting Render backend
        const res = await api.get('/auth/google/status', { timeout: 5000 });
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

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const res = await api.post('/auth/login', {
        ...credentials,
        remember_me: rememberMe,
      });
      const user = res.data?.user || res.data?.data?.user;

      if (!user) {
        toast.error('Login failed. Please check your credentials.');
        return;
      }

      login({
        id: String(user.id),
        name: user.name,
        email: user.email,
        role: user.role,
      }, { remember: rememberMe });

      toast.success('Logged in successfully!');
      navigate(getDashboardRoute(user.role));
    } catch (error: any) {
      console.error(error);
      const errorMsg = error.response?.data?.detail || 'Login failed. Please try again.';
      toast.error(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRoleChange = (role: 'student' | 'counselor' | 'admin') => {
    const demoCredentials = {
      student: { email: 'student@impactai.com', password: 'Student@ImpactAI1!' },
      counselor: { email: 'counselor@impactai.com', password: 'Counselor@ImpactAI1!' },
      admin: { email: 'admin@impactai.com', password: 'Admin@ImpactAI1!' },
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

  const handleAnonymousContinue = () => {
    login(
      {
        id: 'anonymous-session',
        name: 'Anonymous User',
        email: '',
        role: 'student',
        isAnonymous: true,
      },
      { remember: false, anonymous: true }
    );
    toast.success('Anonymous support mode is ready.');
    navigate('/app/booking?mode=anonymous', { replace: true });
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
      <div className="min-h-screen bg-[#FFE17C] lg:grid lg:grid-cols-[.82fr_1.18fr]">
        <aside className="hidden lg:flex flex-col justify-between border-r-2 border-black bg-[#171E19] p-10 text-white dot-pattern">
          <Link to="/" className="inline-flex"><img src="/ImpactAI_logo.png" alt="ImpactAI" className="h-12 w-auto bg-white px-3 py-1 border-2 border-white" /></Link>
          <div>
            <span className="text-sm font-black uppercase tracking-[.16em] text-[#FFE17C]">A steady place to begin</span>
            <h1 className="mt-4 max-w-lg text-6xl font-black leading-[.92] !text-white">YOUR SPACE.<br/>YOUR PACE.</h1>
            <p className="mt-6 max-w-md text-lg leading-relaxed text-[#B7C6C2]">Talk with Zenith, notice how you feel and find the support that fits today.</p>
          </div>
          <p className="text-sm text-[#B7C6C2]">Zenith supports wellbeing. It does not diagnose or replace professional care.</p>
        </aside>
        <main className="flex min-h-screen items-center justify-center p-4 sm:p-8">
          <div className="w-full max-w-[520px]">
            <div className="mb-6 flex items-center justify-between lg:hidden">
              <Link to="/"><img src="/ImpactAI_logo.png" alt="ImpactAI" className="h-10 w-auto" /></Link>
              <Link to="/signup" className="brutal-outline px-4 py-2 text-sm font-bold">Sign up</Link>
            </div>
            <ScrollFadeIn yOffset={16}>
              <div className="brutal-card-lg p-5 sm:p-8 bg-white">
                <div className="mb-6">
                  <span className="text-xs font-black uppercase tracking-[.16em]">ImpactAI account</span>
                  <h1 className="mt-2 text-4xl font-black">WELCOME BACK.</h1>
                  <p className="mt-2 text-sm text-[#171E19]/70">Choose your role, then sign in.</p>
                </div>

                {/* Role tabs */}
                <Tabs defaultValue="student" className="w-full">
                  <TabsList className="grid w-full grid-cols-3 mb-6 bg-gray-100 rounded-lg p-1">
                    {(['student', 'counselor', 'admin'] as const).map((role) => (
                      <TabsTrigger
                        key={role}
                        value={role}
                        onClick={() => handleRoleChange(role)}
                        className="flex items-center gap-1.5 rounded-[8px] border-2 border-transparent data-[state=active]:border-black data-[state=active]:bg-[#FFE17C] data-[state=active]:text-black data-[state=active]:shadow-[3px_3px_0_#000]"
                      >
                        {getRoleIcon(role)}
                        <span className="hidden sm:inline capitalize">{role}</span>
                      </TabsTrigger>
                    ))}
                  </TabsList>

                  {(['student', 'counselor', 'admin'] as const).map((role) => (
                    <TabsContent key={role} value={role} className="space-y-4">
                      <div className="text-center p-3 bg-[#B7C6C2] rounded-[8px] border-2 border-black">
                        <div className="flex items-center justify-center space-x-2 mb-1 text-[#2F7A6D]">
                          {getRoleIcon(role)}
                          <span className="font-medium capitalize">{role} Portal</span>
                        </div>
                        <p className="text-sm text-gray-500">
                          {getRoleDescription(role)}
                        </p>
                      </div>
                    </TabsContent>
                  ))}
                </Tabs>

                {/* Login form */}
                <form onSubmit={handleLogin} className="space-y-4 mt-6">
                  <div className="space-y-1.5">
                    <Label htmlFor="email" className="text-gray-700 font-medium">Email</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="email"
                        type="email"
                        placeholder="Enter your email"
                        value={credentials.email}
                        onChange={(e) =>
                          setCredentials({ ...credentials, email: e.target.value })
                        }
                        className="pl-10 brutal-input"
                        required
                      />
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="password" className="text-gray-700 font-medium">Password</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="password"
                        type={showPassword ? 'text' : 'password'}
                        placeholder="Enter your password"
                        value={credentials.password}
                        onChange={(e) =>
                          setCredentials({ ...credentials, password: e.target.value })
                        }
                        className="pl-10 pr-12 brutal-input"
                        required
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword((value) => !value)}
                        className="absolute right-3 top-3 text-[#171E19]/60 hover:text-[#171E19]"
                        aria-label={showPassword ? 'Hide password' : 'Show password'}
                      >
                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>

                  {/* Remember me */}
                  <div className="flex items-center justify-between rounded-lg border border-gray-100 bg-gray-50 px-3 py-2">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="remember-me"
                        checked={rememberMe}
                        onCheckedChange={(checked) => setRememberMe(Boolean(checked))}
                        className="border-gray-300 data-[state=checked]:bg-[#2F7A6D] data-[state=checked]:border-[#2F7A6D]"
                      />
                      <Label htmlFor="remember-me" className="cursor-pointer text-sm text-gray-600">
                        Remember me on this device
                      </Label>
                    </div>
                    <span className="text-xs text-gray-400">
                      {rememberMe ? 'Persistent session' : 'Session only'}
                    </span>
                  </div>

                  <Button
                    type="submit"
                    size="lg"
                    className="brutal-button w-full"
                    disabled={isLoading}
                  >
                    {isLoading ? 'Signing In...' : 'Sign In'}
                  </Button>
                </form>

                {/* Google sign-in */}
                <div title={!isGoogleEnabled && !isCheckingGoogleAuth ? 'Google sign-in is not configured on this instance' : undefined}>
                  <Button
                    onClick={handleGoogleLogin}
                    variant="outline"
                    size="lg"
                    className="w-full mt-4 flex items-center justify-center gap-2 border-gray-200 hover:border-[#2F7A6D] hover:text-[#2F7A6D] rounded-lg transition-colors"
                    disabled={isCheckingGoogleAuth}
                  >
                    <FaGoogle className="h-4 w-4" />
                    <span>
                      {isCheckingGoogleAuth
                        ? 'Checking Google Sign-In...'
                        : 'Sign in with Google'}
                    </span>
                  </Button>
                </div>

                {/* Anonymous mode */}
                <div className="mt-4 border border-dashed border-[#2F7A6D]/30 bg-teal-50/50 rounded-xl p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h3 className="font-semibold text-gray-800">Continue anonymously</h3>
                      <p className="mt-1 text-sm text-gray-500">
                        Jump straight into anonymous support and private booking without exposing
                        your identity.
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleAnonymousContinue}
                      className="shrink-0 border-[#2F7A6D]/40 text-[#2F7A6D] hover:bg-[#2F7A6D] hover:text-white transition-colors"
                    >
                      Anonymous Mode
                    </Button>
                  </div>
                </div>

                {/* Sign-up link */}
                <div className="mt-6 text-center text-sm">
                  <span className="text-gray-500">Don't have an account? </span>
                  <Link to="/signup" className="text-[#2F7A6D] hover:underline font-medium">
                    Sign up
                  </Link>
                </div>
              </div>
            </ScrollFadeIn>
            <p className="mt-5 text-center text-xs font-medium text-[#171E19]/70">For immediate danger, contact local emergency services.</p>
          </div>
        </main>
      </div>
    </PageTransition>
  );
};

export default Login;
