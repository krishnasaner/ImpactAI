import React from 'react';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { Toaster as Sonner } from '@/components/ui/sonner';
import { TooltipProvider } from '@/components/ui/tooltip';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Navigate, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { MusicProvider } from '@/contexts/MusicContext';
import { AuthProvider } from '@/contexts/AuthContext';
import Layout from '@/components/layout/Layout';
import ChatWidget from '@/components/chat/ChatWidget';
import NotificationContainer from '@/components/notifications/NotificationContainer';
import { ErrorBoundary } from '@/components/error';
import ScrollToTop from './components/layout/scrollToTop';
import Signup from './pages/Signup';
import ProtectedRoute from './contexts/ProtectedRoutes';

const Index = React.lazy(() => import('./pages/PublicLanding'));
const Login = React.lazy(() => import('./pages/Login'));
const InstitutionSelection = React.lazy(() => import('./pages/InstitutionSelection'));
const Resources = React.lazy(() => import('./pages/Resources'));
const Forum = React.lazy(() => import('./pages/Forum'));
const Booking = React.lazy(() => import('./pages/Booking'));
const Dashboard = React.lazy(() => import('./pages/admin-Dashboard'));
const StudentDashboard = React.lazy(() => import('./pages/StudentDashboard'));
const Profile = React.lazy(() => import('./pages/Profile'));
const SystemHealth = React.lazy(() => import('./pages/SystemHealth'));
const UserManagement = React.lazy(() => import('./pages/UserManagement'));
const ContentModeration = React.lazy(() => import('./pages/ContentModeration'));
const Sessions = React.lazy(() => import('./pages/Sessions'));
const AIChat = React.lazy(() => import('./pages/AIChat'));
const BreathingExercises = React.lazy(() => import('./pages/BreathingExercises'));
const NotificationSettings = React.lazy(() => import('./components/settings/NotificationSettings'));
const EnhancedThemeSettings = React.lazy(() => import('./components/settings/EnhancedThemeSettings'));
const About = React.lazy(() => import('./pages/About'));
const NotFound = React.lazy(() => import('./pages/NotFound'));
const ContactUs = React.lazy(() => import('./pages/ContactUs'));
const MentalHealthBlog = React.lazy(() => import('./pages/MentalHealthBlog'));
const PrivacyPolicy = React.lazy(() => import('./pages/PrivacyPolicy'));
const TermsOfService = React.lazy(() => import('./pages/TermsOfService'));

const queryClient = new QueryClient();

const getDashboardPath = () => {
  const role = sessionStorage.getItem('userRole') || localStorage.getItem('userRole');
  return role === 'admin' || role === 'counselor'
    ? '/app/admin-dashboard'
    : '/app/student-dashboard';
};

const DashboardRedirect = () => <Navigate to={getDashboardPath()} replace />;

const App = () => (
  <ErrorBoundary componentName="AppRoot" variant="page">
    <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <MusicProvider>
            <AuthProvider>
              <TooltipProvider>
                <ToastContainer
                  position="top-right"
                  autoClose={3000}
                  hideProgressBar={false}
                  newestOnTop={false}
                  closeOnClick
                  rtl={false}
                  pauseOnFocusLoss
                  draggable
                  pauseOnHover
                  theme="colored"
                  aria-label="Toast notifications"
                />
                <Sonner />
                <BrowserRouter>
                  <React.Suspense
                    fallback={
                      <div className="flex items-center justify-center min-h-screen">
                        <div className="space-y-4 text-center">
                          <div className="animate-pulse">
                            <div className="w-8 h-8 bg-primary/20 rounded-full mx-auto mb-2" />
                            <div className="text-muted-foreground">Loading Impact AI...</div>
                          </div>
                        </div>
                      </div>
                    }
                  >
                    <Routes>
                      <Route path="/about" element={<About />} />
                      <Route path="/login" element={<Login />} />
                      <Route path="/signup" element={<Signup />} />
                      <Route path="/register" element={<Navigate to="/signup" replace />} />
                      <Route path="/privacy" element={<PrivacyPolicy />} />
                      <Route path="/terms" element={<TermsOfService />} />
                      <Route path="/cookies" element={<Navigate to="/privacy#cookies" replace />} />
                      <Route path="/select-institution" element={<InstitutionSelection />} />
                      <Route path="/" element={<Index />} />
                      <Route path="/contact" element={<ContactUs />} />
                      <Route path="/privacy" element={<PrivacyPolicy />} />
                      <Route path="/terms" element={<TermsOfService />} />
                      <Route path="/register" element={<Navigate to="/signup" replace />} />
                      <Route path="*" element={<NotFound />} />

                      {/* Protected Routes */}
                      <Route
                        path="/app"
                        element={
                          <ProtectedRoute>
                            <Layout />
                          </ProtectedRoute>
                        }
                      >
                        <Route index element={<DashboardRedirect />} />
                        <Route path="dashboard" element={<DashboardRedirect />} />
                        <Route path="admin-dashboard" element={<Dashboard />} />
                        <Route path="student-dashboard" element={<StudentDashboard />} />
                        <Route path="mood" element={<Navigate to="/app/student-dashboard#check-in" replace />} />
                        <Route path="settings" element={<Navigate to="/app/theme-settings" replace />} />
                        <Route path="resources" element={<Resources />} />
                        <Route path="forum" element={<Forum />} />
                        <Route path="blog" element={<MentalHealthBlog />} />
                        <Route path="booking" element={<Booking />} />
                        <Route path="profile" element={<Profile />} />
                        <Route path="sessions" element={<Sessions />} />
                        <Route path="breathing" element={<BreathingExercises />} />
                        <Route path="notifications" element={<NotificationSettings />} />
                        <Route path="theme-settings" element={<EnhancedThemeSettings />} />
                        <Route path="system" element={<SystemHealth />} />
                        <Route path="users" element={<UserManagement />} />
                        <Route path="moderation" element={<ContentModeration />} />
                        <Route path="chat" element={<AIChat />} />

                        <Route path="*" element={<NotFound />} />
                        {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
                      </Route>
                    </Routes>
                  </React.Suspense>
                  <ChatWidget />
                  <NotificationContainer />
                  <ScrollToTop />
                </BrowserRouter>
              </TooltipProvider>
            </AuthProvider>
          </MusicProvider>
        </ThemeProvider>
      </QueryClientProvider>
  </ErrorBoundary>
);

export default App;
