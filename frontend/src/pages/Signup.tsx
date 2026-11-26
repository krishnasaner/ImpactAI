import { useEffect, useState } from 'react';
import { toast } from 'react-toastify';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Heart, Mail, Lock, User, Shield, GraduationCap, Eye, EyeOff } from 'lucide-react';
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
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

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
      import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000`;
    window.location.href = `${API_BASE_URL}/auth/google?role=${credentials.role}&next=signup`;
  };

  return (
    <PageTransition>
      <div className="min-h-screen bg-[#FFE17C] dot-pattern flex items-center justify-center p-4">
        <div className="w-full max-w-md space-y-6">
          {/* Logo & tagline */}
          <ScrollFadeIn yOffset={20}>
            <div className="text-center space-y-2">
              <Link to="/" className="inline-block">
                <img
                  src="/ImpactAI_logo.png"
                  alt="ImpactAI Logo"
                  className="h-14 md:h-16 w-auto max-w-[190px] mx-auto mb-2 bg-white px-3 py-1.5 border-2 border-black rounded shadow-[3px_3px_0_#000] object-contain"
                />
              </Link>
              <p className="text-gray-500 text-sm">Your trusted mental health companion</p>
            </div>
          </ScrollFadeIn>

          {/* Card */}
          <ScrollFadeIn yOffset={16} delay={0.07}>
            <div className="brutal-card-lg bg-white p-5 sm:p-8">
              {/* Card header */}
              <div className="text-center mb-6">
                <h1 className="text-2xl font-bold text-gray-900">Create Your Account</h1>
                <p className="text-gray-500 text-sm mt-1">
                  Choose your role to get started
                </p>
              </div>

              {/* Role tabs */}
              <Tabs defaultValue="student" className="w-full">
                <TabsList className="grid w-full grid-cols-3 mb-6 bg-gray-100 rounded-lg p-1">
                  {(['student', 'counselor', 'admin'] as const).map((role) => (
                    <TabsTrigger
                      key={role}
                      value={role}
                      onClick={() => handleRoleChange(role)}
                      className="flex items-center gap-1.5 rounded-[8px] border-2 border-transparent data-[state=active]:border-black data-[state=active]:bg-[#FFE17C] data-[state=active]:text-black data-[state=active]:shadow-[3px_3px_0_#000] transition-all"
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

              {/* Signup form */}
              <form onSubmit={handleSignup} className="space-y-4 mt-6">
                {/* Email */}
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

                {/* Password */}
                <div className="space-y-1.5">
                  <Label htmlFor="password" className="text-gray-700 font-medium">Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="Create a strong password"
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
                  <p className="text-xs text-gray-400">
                    Min. 12 chars · uppercase · lowercase · number · special character
                  </p>
                </div>

                {/* Confirm password */}
                <div className="space-y-1.5">
                  <Label htmlFor="confirmPassword" className="text-gray-700 font-medium">Confirm Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="confirmPassword"
                      type="password"
                      placeholder="Confirm your password"
                      value={credentials.confirmPassword || ''}
                      onChange={(e) =>
                        setCredentials({ ...credentials, confirmPassword: e.target.value })
                      }
                      className="pl-10 brutal-input"
                      required
                    />
                  </div>
                </div>

                {/* Remember me */}
                <div className="flex items-center space-x-2 rounded-lg border border-gray-100 bg-gray-50 px-3 py-2">
                  <input
                    type="checkbox"
                    id="rememberMe"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="h-4 w-4 rounded border-gray-300 text-[#2F7A6D] focus:ring-[#2F7A6D] accent-[#2F7A6D]"
                  />
                  <Label htmlFor="rememberMe" className="text-sm text-gray-600 cursor-pointer">
                    Remember Me
                  </Label>
                </div>

                <Button
                  type="submit"
                  size="lg"
                  className="brutal-button w-full"
                  disabled={loading}
                >
                  {loading ? 'Signing Up...' : 'Create Account'}
                </Button>
              </form>

              {/* Google sign-up */}
              <div title={!isGoogleEnabled && !isCheckingGoogleAuth ? 'Google sign-up is not configured on this instance' : undefined}>
                <Button
                  onClick={handleGoogleSignup}
                  variant="outline"
                  size="lg"
                  className="w-full mt-4 flex items-center justify-center gap-2 border-gray-200 hover:border-[#2F7A6D] hover:text-[#2F7A6D] rounded-lg transition-colors"
                  disabled={isCheckingGoogleAuth}
                >
                  <FaGoogle className="h-4 w-4" />
                  <span>
                    {isCheckingGoogleAuth
                      ? 'Checking Google Sign-Up...'
                      : 'Sign up with Google'}
                  </span>
                </Button>
              </div>

              {/* Log in link */}
              <div className="mt-6 text-center text-sm">
                <span className="text-gray-500">Already have an account? </span>
                <Link to="/login" className="text-[#2F7A6D] hover:underline font-medium">
                  Log in
                </Link>
              </div>
            </div>
          </ScrollFadeIn>

          {/* Trust signals */}
          <ScrollFadeIn delay={0.11}>
            <div className="text-center space-y-1 text-xs text-gray-400">
              <p>Zenith provides support, not diagnosis or emergency care.</p>
            </div>
          </ScrollFadeIn>
        </div>
      </div>
    </PageTransition>
  );
};

export default Signup;
