import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/contexts/AuthContext';
import {
  MessageCircle,
  Calendar,
  BookOpen,
  Users,
  Heart,
  CheckCircle,
  Wind,
  Bell,
  Smile,
  Phone,
  Shield,
  Brain,
  Clock,
  ChevronRight,
  Menu,
  X,
  Home,
  Settings,
  LogOut,
  User,
  Lightbulb,
  ArrowRight,
} from 'lucide-react';
import React, { useState, useEffect } from 'react';

// Import functional components
import { MoodTracker } from '@/components/dashboard/MoodTracker';
import QuickMoodCheckIn from '@/components/dashboard/QuickMoodCheckIn';
import {
  MoodSummaryWidget,
  MoodTrendWidget,
  MoodStreakWidget,
  MoodWeeklyWidget,
} from '@/components/dashboard/MoodWidgets';
import FloatingMoodButton from '@/components/dashboard/FloatingMoodButton';
import MoodAnalytics from '@/components/dashboard/MoodAnalytics';
import { GoalsTracker } from '@/components/dashboard/GoalsTracker';
import { ActivityTracker, AchievementTracker } from '@/components/dashboard/ActivityTracker';
import EnhancedDailyTips from '@/components/dashboard/EnhancedDailyTips';
import { InteractiveAnalytics } from '@/components/dashboard/InteractiveAnalytics';
import {
  useActivityLog,
  useAchievements,
  useMoodTracking,
  useGoals,
} from '@/hooks/useDashboardFeatures';

// ─── Sidebar nav items ────────────────────────────────────────────────────────
const NAV_ITEMS = [
  { label: 'Dashboard', icon: Home, href: '/app/dashboard' },
  { label: 'AI Chat (Zenith)', icon: MessageCircle, href: '/app/chat' },
  { label: 'Mood Tracker', icon: Smile, href: '/app/mood' },
  { label: 'Book Counselling', icon: Calendar, href: '/app/booking' },
  { label: 'Resources', icon: BookOpen, href: '/app/resources' },
  { label: 'Community', icon: Users, href: '/app/forum' },
  { label: 'Breathing', icon: Wind, href: '/app/breathing' },
];

// ─── Sidebar ──────────────────────────────────────────────────────────────────
const Sidebar = ({
  open,
  onClose,
  userName,
}: {
  open: boolean;
  onClose: () => void;
  userName: string;
}) => {
  const pathname = window.location.pathname;

  return (
    <>
      {/* Overlay (mobile) */}
      {open && (
        <div
          className="fixed inset-0 bg-black/40 z-30 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar panel */}
      <aside
        className={`
          fixed top-0 left-0 h-full w-64 bg-white border-r border-gray-100 shadow-lg z-40 flex flex-col
          transition-transform duration-300
          ${open ? 'translate-x-0' : '-translate-x-full'}
          lg:translate-x-0 lg:static lg:shadow-none lg:z-auto
        `}
      >
        {/* Logo */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <Link to="/app/dashboard" className="flex items-center gap-2" onClick={onClose}>
            <img src="/ImpactAI_logo.png" alt="ImpactAI" className="h-8 w-auto" />
            <span className="font-bold text-[#2F7A6D] text-lg">ImpactAI</span>
          </Link>
          <button
            className="lg:hidden text-gray-400 hover:text-gray-600"
            onClick={onClose}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Nav links */}
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
          {NAV_ITEMS.map(({ label, icon: Icon, href }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                to={href}
                onClick={onClose}
                className={`
                  flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
                  ${active
                    ? 'bg-[#2F7A6D]/10 text-[#2F7A6D]'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-[#2F7A6D]'
                  }
                `}
              >
                <Icon className="h-4 w-4 flex-shrink-0" />
                {label}
              </Link>
            );
          })}
        </nav>

        {/* User chip */}
        <div className="px-4 py-4 border-t border-gray-100">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-full bg-[#2F7A6D]/10 flex items-center justify-center">
              <User className="h-4 w-4 text-[#2F7A6D]" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-800 truncate">{userName}</p>
              <p className="text-xs text-gray-400">Student</p>
            </div>
            <Link to="/app/settings" className="text-gray-400 hover:text-gray-600">
              <Settings className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </aside>
    </>
  );
};

// ─── Top bar ──────────────────────────────────────────────────────────────────
const TopBar = ({
  onMenuClick,
  pageTitle,
  userName,
}: {
  onMenuClick: () => void;
  pageTitle: string;
  userName: string;
}) => (
  <header className="sticky top-0 z-20 bg-white border-b border-gray-100 shadow-sm flex items-center justify-between px-4 py-3">
    <div className="flex items-center gap-3">
      <button
        className="lg:hidden text-gray-500 hover:text-[#2F7A6D] transition-colors"
        onClick={onMenuClick}
        aria-label="Open menu"
      >
        <Menu className="h-6 w-6" />
      </button>
      <h1 className="text-lg font-semibold text-gray-800">{pageTitle}</h1>
    </div>
    <div className="flex items-center gap-3">
      <Link
        to="/app/notifications"
        className="relative text-gray-500 hover:text-[#2F7A6D] transition-colors"
        aria-label="Notifications"
      >
        <Bell className="h-5 w-5" />
        <span className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-[#FFB400]" />
      </Link>
      <div className="flex items-center gap-2">
        <div className="h-8 w-8 rounded-full bg-[#2F7A6D]/10 flex items-center justify-center">
          <User className="h-4 w-4 text-[#2F7A6D]" />
        </div>
        <span className="hidden sm:block text-sm font-medium text-gray-700">
          {userName.split(' ')[0]}
        </span>
      </div>
    </div>
  </header>
);

// ─── Quick action card ────────────────────────────────────────────────────────
const QuickActionCard = ({
  title,
  description,
  icon: Icon,
  href,
  iconBg = 'bg-[#2F7A6D]',
  onClick,
}: {
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  href: string;
  iconBg?: string;
  onClick?: () => void;
}) => (
  <Link
    to={href}
    onClick={onClick}
    className="bg-white border border-gray-100 rounded-xl shadow-sm p-5 flex flex-col gap-4 hover:-translate-y-0.5 transition-transform cursor-pointer group"
  >
    <div className={`${iconBg} rounded-xl p-3 w-fit`}>
      <Icon className="h-5 w-5 text-white" />
    </div>
    <div>
      <p className="font-semibold text-gray-800 group-hover:text-[#2F7A6D] transition-colors text-sm">
        {title}
      </p>
      <p className="text-xs text-gray-500 mt-1 leading-relaxed">{description}</p>
    </div>
    <div className="flex items-center text-xs text-[#2F7A6D] font-medium mt-auto">
      Open <ArrowRight className="h-3 w-3 ml-1 group-hover:translate-x-1 transition-transform" />
    </div>
  </Link>
);

// ─── Institution badge ────────────────────────────────────────────────────────
interface Institution {
  name: string;
  location?: string;
  type?: string;
  id?: string;
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────
const StudentDashboard = () => {
  const { user } = useAuth();
  const [selectedInstitution, setSelectedInstitution] = useState<Institution | null>(null);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [motivationalMessage, setMotivationalMessage] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Functional hooks — preserved exactly
  const { logActivity } = useActivityLog();
  const { checkAchievements } = useAchievements();
  const { moods } = useMoodTracking();
  const { goals } = useGoals();

  // Handler for action card clicks — preserved exactly
  const handleActionCardClick = (href: string, title: string) => {
    const activityTypes: Record<string, 'chat' | 'resource' | 'forum' | 'booking'> = {
      '/app/chat': 'chat',
      '/app/booking': 'booking',
      '/app/resources': 'resource',
      '/app/forum': 'forum',
    };

    const activityType = activityTypes[href];
    if (activityType) {
      logActivity(activityType, `Clicked ${title}`, `Navigated to ${title} from dashboard`);
    }
  };

  useEffect(() => {
    // Load selected institution from localStorage
    const institution = localStorage.getItem('selected_institution');
    if (institution) {
      setSelectedInstitution(JSON.parse(institution));
    }

    const getMotivationalMessage = () => {
      const messages = [
        'Your mental health matters. Take it one day at a time.',
        "You're stronger than you think. Keep moving forward.",
        'Every step toward wellness is a victory worth celebrating.',
        'Remember to be kind to yourself today.',
        'Your journey to better mental health starts with small steps.',
        'Progress, not perfection. Every small step counts.',
        'You have the strength to overcome any challenge today.',
        'Taking care of your mental health is a sign of strength.',
        'Today is a new opportunity to prioritize your wellbeing.',
        'You deserve happiness, peace, and self-compassion.',
      ];

      const today = new Date().toDateString();
      const savedMessage = localStorage.getItem(`motivational_message_${today}`);

      if (savedMessage) {
        return savedMessage;
      } else {
        const dateNumber = new Date().getDate() + new Date().getMonth();
        const messageIndex = dateNumber % messages.length;
        const todayMessage = messages[messageIndex];
        localStorage.setItem(`motivational_message_${today}`, todayMessage);
        return todayMessage;
      }
    };

    setMotivationalMessage(getMotivationalMessage());

    const timer = setInterval(() => setCurrentTime(new Date()), 60000);

    logActivity('resource', 'Visited Student Dashboard', 'Dashboard access');

    const activities = JSON.parse(localStorage.getItem('activity_log') || '[]');
    checkAchievements(activities, moods, goals);

    return () => clearInterval(timer);
  }, [logActivity, checkAchievements, moods, goals]);

  const getGreeting = () => {
    const formattedHour = new Intl.DateTimeFormat('en-IN', {
      hour: 'numeric',
      hour12: false,
      timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    }).format(currentTime);
    const hour = Number.parseInt(formattedHour, 10);
    if (hour < 12) return 'Good Morning';
    if (hour < 17) return 'Good Afternoon';
    return 'Good Evening';
  };

  const firstName = user?.name?.split(' ')[0] ?? 'there';
  const fullName = user?.name ?? 'Student';

  return (
    <div className="min-h-screen bg-[#F5F5F5] flex">
      {/* ── Sidebar ── */}
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        userName={fullName}
      />

      {/* ── Main area ── */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <TopBar
          onMenuClick={() => setSidebarOpen(true)}
          pageTitle="Dashboard"
          userName={fullName}
        />

        {/* Scrollable content */}
        <main className="flex-1 overflow-y-auto px-4 sm:px-6 py-6 space-y-6 max-w-7xl mx-auto w-full">

          {/* ── Welcome banner ── */}
          <div className="bg-gradient-to-r from-[#2F7A6D]/10 via-white to-blue-50 border border-gray-100 rounded-xl shadow-sm p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Smile className="h-5 w-5 text-[#2F7A6D]" />
                <span className="text-xs font-medium text-[#2F7A6D] uppercase tracking-wide">
                  {getGreeting()}
                </span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold text-gray-900">
                {getGreeting()}, <span className="text-[#2F7A6D]">{firstName}</span> 👋
              </h2>
              <p className="text-gray-500 mt-1 max-w-xl text-sm leading-relaxed">
                {motivationalMessage || 'Welcome to your wellness journey…'}
              </p>
              {selectedInstitution && (
                <Badge
                  variant="outline"
                  className="mt-3 text-xs border-[#2F7A6D]/30 text-[#2F7A6D]"
                >
                  {selectedInstitution.name} Student
                </Badge>
              )}
            </div>
            <div className="flex gap-2 flex-shrink-0">
              <Button
                asChild
                className="bg-[#2F7A6D] hover:bg-teal-700 text-white text-sm"
              >
                <Link
                  to="/app/chat"
                  onClick={() =>
                    logActivity('chat', 'Started Zenith chat from banner', 'Welcome banner CTA')
                  }
                >
                  <MessageCircle className="h-4 w-4 mr-2" />
                  Chat with Zenith
                </Link>
              </Button>
              <Button
                asChild
                variant="outline"
                className="border-[#2F7A6D]/30 text-[#2F7A6D] hover:bg-[#2F7A6D]/5 text-sm"
              >
                <Link to="/app/mood">
                  <Heart className="h-4 w-4 mr-2" />
                  Track Mood
                </Link>
              </Button>
            </div>
          </div>

          {/* ── Quick action cards ── */}
          <section>
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Quick Actions
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <QuickActionCard
                title="Chat with Zenith"
                description="Instant AI mental health support, available 24/7"
                icon={MessageCircle}
                href="/app/chat"
                iconBg="bg-[#2F7A6D]"
                onClick={() => handleActionCardClick('/app/chat', 'Chat with Zenith')}
              />
              <QuickActionCard
                title="Track Mood"
                description="Log how you're feeling and spot patterns over time"
                icon={Smile}
                href="/app/mood"
                iconBg="bg-[#4A90E2]"
                onClick={() => handleActionCardClick('/app/mood', 'Track Mood')}
              />
              <QuickActionCard
                title="Book Counselling"
                description="Schedule a session with a licensed professional"
                icon={Calendar}
                href="/app/booking"
                iconBg="bg-amber-500"
                onClick={() => handleActionCardClick('/app/booking', 'Book Counselling')}
              />
              <QuickActionCard
                title="Browse Resources"
                description="Evidence-based tools, meditations & coping guides"
                icon={BookOpen}
                href="/app/resources"
                iconBg="bg-purple-500"
                onClick={() => handleActionCardClick('/app/resources', 'Browse Resources')}
              />
            </div>
          </section>

          {/* ── Mood check-in row ── */}
          <section>
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Mood Check-In
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="md:col-span-2">
                <QuickMoodCheckIn variant="default" showStreak={true} />
              </div>
              <MoodSummaryWidget />
              <MoodStreakWidget />
            </div>
          </section>

          {/* ── Mood trend / weekly ── */}
          <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <MoodTrendWidget />
            <MoodWeeklyWidget />
            <MoodAnalytics timeframe="week" />
          </section>

          {/* ── Wellness journey ── */}
          <section>
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Your Wellness Journey
            </h3>
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
              <div className="xl:col-span-2">
                <InteractiveAnalytics />
              </div>
              <MoodTracker />
              <GoalsTracker />
              <ActivityTracker />
              <AchievementTracker />
            </div>
          </section>

          {/* ── Daily tips ── */}
          <section>
            <EnhancedDailyTips />
          </section>

          {/* ── Wellness tools row ── */}
          <section>
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Wellness Tools
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Breathing exercises */}
              <div className="bg-white border border-gray-100 rounded-xl shadow-sm p-5 hover:-translate-y-0.5 transition-transform">
                <div className="flex items-start gap-4">
                  <div className="bg-blue-100 rounded-xl p-3 flex-shrink-0">
                    <Wind className="h-6 w-6 text-blue-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-gray-800">Breathing Exercises</p>
                    <p className="text-sm text-gray-500 mt-1 mb-3 leading-relaxed">
                      Quick breathing techniques to reduce stress and improve focus
                    </p>
                    <ul className="space-y-1 mb-4">
                      {['4-7-8 breathing for anxiety', 'Box breathing for focus', 'Guided sessions (1-10 min)'].map((f) => (
                        <li key={f} className="flex items-center text-xs text-gray-500">
                          <CheckCircle className="h-3 w-3 text-blue-500 mr-2 flex-shrink-0" />
                          {f}
                        </li>
                      ))}
                    </ul>
                    <Button asChild className="bg-blue-600 hover:bg-blue-700 text-white text-sm">
                      <Link to="/app/breathing">
                        <Wind className="h-4 w-4 mr-2" />
                        Start Exercise
                      </Link>
                    </Button>
                  </div>
                </div>
              </div>

              {/* Wellness reminders */}
              <div className="bg-white border border-gray-100 rounded-xl shadow-sm p-5 hover:-translate-y-0.5 transition-transform">
                <div className="flex items-start gap-4">
                  <div className="bg-purple-100 rounded-xl p-3 flex-shrink-0">
                    <Bell className="h-6 w-6 text-purple-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-gray-800">Wellness Reminders</p>
                    <p className="text-sm text-gray-500 mt-1 mb-3 leading-relaxed">
                      Customize mood check-in, breathing, and session reminders
                    </p>
                    <ul className="space-y-1 mb-4">
                      {['Daily mood reminders', 'Breathing exercise alerts', 'Session reminders'].map((f) => (
                        <li key={f} className="flex items-center text-xs text-gray-500">
                          <CheckCircle className="h-3 w-3 text-purple-500 mr-2 flex-shrink-0" />
                          {f}
                        </li>
                      ))}
                    </ul>
                    <Button
                      asChild
                      variant="outline"
                      className="border-purple-200 text-purple-700 hover:bg-purple-50 text-sm"
                    >
                      <Link to="/app/notifications">
                        <Settings className="h-4 w-4 mr-2" />
                        Manage Reminders
                      </Link>
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* ── Immediate support CTA ── */}
          <section className="bg-gradient-to-r from-[#2F7A6D]/5 to-[#4A90E2]/5 border border-[#2F7A6D]/20 rounded-xl shadow-sm p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <h3 className="font-bold text-gray-800 flex items-center gap-2 mb-1">
                <Lightbulb className="h-5 w-5 text-[#2F7A6D]" />
                Need immediate support?
              </h3>
              <p className="text-sm text-gray-500">
                Zenith is available 24/7 for instant mental health assistance
              </p>
            </div>
            <div className="flex gap-3 flex-shrink-0">
              <Button asChild className="bg-[#2F7A6D] hover:bg-teal-700 text-white text-sm">
                <Link
                  to="/app/chat"
                  onClick={() =>
                    logActivity('chat', 'Started Zenith chat from quick access', 'Dashboard quick access button')
                  }
                >
                  <MessageCircle className="h-4 w-4 mr-2" />
                  Start Zenith
                </Link>
              </Button>
              <Button
                asChild
                variant="outline"
                className="border-[#2F7A6D]/30 text-[#2F7A6D] hover:bg-[#2F7A6D]/5 text-sm"
              >
                <Link
                  to="/app/booking"
                  onClick={() =>
                    logActivity('booking', 'Started booking from quick access', 'Dashboard quick access button')
                  }
                >
                  <Calendar className="h-4 w-4 mr-2" />
                  Book Session
                </Link>
              </Button>
            </div>
          </section>

          {/* ── Crisis / Emergency support ── */}
          <section className="bg-red-50 border border-red-200 rounded-xl p-5 sm:p-6">
            <div className="text-center space-y-5">
              <div className="flex items-center justify-center gap-3">
                <div className="p-2.5 rounded-full bg-red-100">
                  <Shield className="h-5 w-5 text-red-600" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-red-800">Crisis Support Available</h3>
                  <div className="h-0.5 w-12 bg-red-400 rounded-full mx-auto mt-1" />
                </div>
              </div>

              <p className="text-sm text-red-700 leading-relaxed max-w-2xl mx-auto">
                If you're experiencing a mental health crisis, having thoughts of self-harm, or need
                immediate support, please reach out right away. You are not alone — help is
                available across India right now.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 max-w-2xl mx-auto">
                <Button
                  variant="destructive"
                  size="sm"
                  className="bg-red-600 hover:bg-red-700 text-white"
                  onClick={() => window.open('tel:14416', '_self')}
                >
                  <Phone className="h-4 w-4 mr-2" />
                  Tele-MANAS: 14416
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="border-red-300 text-red-700 hover:bg-red-100"
                  onClick={() => window.open('tel:+912227546669', '_self')}
                >
                  <MessageCircle className="h-4 w-4 mr-2" />
                  AASRA: +91 22 2754 6669
                </Button>
                <Button
                  asChild
                  variant="outline"
                  size="sm"
                  className="border-red-300 text-red-700 hover:bg-red-100"
                >
                  <Link
                    to="/app/chat"
                    onClick={() =>
                      logActivity('chat', 'Emergency Zenith chat', 'Crisis support - Emergency Zenith chat accessed')
                    }
                  >
                    <Brain className="h-4 w-4 mr-2" />
                    Emergency Zenith
                  </Link>
                </Button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-red-200 text-sm">
                <div className="text-center space-y-1">
                  <p className="font-semibold text-red-800 flex items-center justify-center gap-1">
                    <Clock className="h-4 w-4" /> Campus Counseling
                  </p>
                  <p className="text-red-600 text-xs">
                    Contact your campus counseling center for professional support
                  </p>
                </div>
                <div className="text-center space-y-1">
                  <p className="font-semibold text-red-800 flex items-center justify-center gap-1">
                    <Heart className="h-4 w-4" /> Peer Support
                  </p>
                  <p className="text-red-600 text-xs">
                    Join our anonymous peer support community for shared experiences
                  </p>
                </div>
              </div>
            </div>
          </section>

        </main>
      </div>

      {/* Floating Mood Button */}
      <FloatingMoodButton position="bottom-right" showOnlyIfNotLogged={false} />
    </div>
  );
};

export default StudentDashboard;
