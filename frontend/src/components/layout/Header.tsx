import { useMemo, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import QuickMoodHeader from '@/components/dashboard/QuickMoodHeader';
import { useAuth } from '@/contexts/AuthContext';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Menu,
  X,
  MessageCircle,
  BookOpen,
  Users,
  BarChart,
  FileText,
  LogOut,
  Settings,
  UserCircle2,
  Shield,
  Bell,
  LucideIcon,
} from 'lucide-react';

type NavItem = {
  name: string;
  href: string;
  icon: LucideIcon;
};

const Header = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const isAppShell = location.pathname.startsWith('/app');

  const navItems: NavItem[] = useMemo(
    () => [
      { name: 'Dashboard', href: '/app/dashboard', icon: BarChart },
      { name: 'Zenith', href: '/app/chat', icon: MessageCircle },
      { name: 'Resources', href: '/app/resources', icon: BookOpen },
      { name: 'Forum', href: '/app/forum', icon: Users },
      { name: 'Anonymous Support', href: '/app/booking?mode=anonymous', icon: Shield },
      { name: 'Blog', href: '/app/blog', icon: FileText },
    ],
    []
  );

  const getInitials = (name?: string) =>
    (name || 'Impact AI')
      .split(' ')
      .map((part) => part[0])
      .join('')
      .slice(0, 2)
      .toUpperCase();

  const isActiveRoute = (href: string) => location.pathname === href.split('?')[0];

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-gray-100 bg-white shadow-sm dark:border-gray-800 dark:bg-gray-950">
      <div className="container flex h-16 items-center justify-between px-6">
        {isAppShell && user ? (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="flex items-center gap-3 rounded-2xl border border-gray-200 bg-white/80 px-3 py-2 text-left transition-all hover:border-primary/40 hover:bg-primary/5 dark:border-gray-800 dark:bg-gray-950/80 dark:hover:border-primary/30">
                <Avatar className="h-10 w-10 border border-primary/20">
                  <AvatarImage src={user.avatar} alt={user.name} />
                  <AvatarFallback className="bg-primary/10 font-semibold text-primary">
                    {getInitials(user.name)}
                  </AvatarFallback>
                </Avatar>
                <div className="hidden sm:block">
                  <div className="text-sm font-semibold text-foreground">
                    {user.isAnonymous ? 'Anonymous Session' : user.name}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {user.isAnonymous ? 'Private support mode' : 'Profile and account'}
                  </div>
                </div>
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-60">
              <DropdownMenuItem asChild>
                <Link to="/app/profile">
                  <UserCircle2 className="mr-2 h-4 w-4" />
                  View profile
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link to="/app/booking?mode=anonymous">
                  <Shield className="mr-2 h-4 w-4" />
                  Continue anonymously
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link to="/app/theme-settings">
                  <Settings className="mr-2 h-4 w-4" />
                  Appearance settings
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link to="/app/notifications">
                  <Bell className="mr-2 h-4 w-4" />
                  Notifications
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        ) : (
          <Link
            to="/"
            className="flex items-center shrink-0 group transition-all duration-300 hover:opacity-80"
          >
            <img
              src="/ImpactAI_logo.png"
              alt="Impact AI"
              className="h-12 md:h-14 w-auto object-contain"
            />
          </Link>
        )}

        {isAppShell && (
          <nav className="ml-10 hidden items-center space-x-1 text-sm font-medium lg:flex">
            {navItems.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className={`rounded-lg px-3 py-2 transition-colors duration-200 ${
                  isActiveRoute(item.href)
                    ? 'bg-primary/10 text-primary'
                    : 'text-gray-500 hover:bg-gray-50 hover:text-blue-600 dark:text-gray-400 dark:hover:bg-gray-900 dark:hover:text-blue-400'
                }`}
              >
                <span>{item.name}</span>
              </Link>
            ))}
          </nav>
        )}

        <div className="flex items-center space-x-3">
          {isAppShell && (
            <div className="hidden md:block">
              <QuickMoodHeader variant="dropdown" showTrend={false} />
            </div>
          )}

          {isAppShell && (
            <div className="hidden sm:block">
              <ThemeToggle />
            </div>
          )}

          {isAppShell && user && (
            <Button variant="outline" className="hidden md:inline-flex" onClick={handleLogout}>
              <LogOut className="mr-2 h-4 w-4" />
              Log out
            </Button>
          )}

          {isAppShell && (
            <Button
              variant="ghost"
              size="icon"
              className="rounded-lg lg:hidden"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            >
              {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
          )}
        </div>
      </div>

      {isMobileMenuOpen && (
        <div className="border-t border-gray-100 bg-white dark:border-gray-800 dark:bg-gray-950 lg:hidden">
          <div className="container px-6 py-4">
            <nav className="flex flex-col space-y-1">
              {isAppShell &&
                navItems.map((item) => (
                  <Link
                    key={item.name}
                    to={item.href}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className="flex items-center space-x-3 rounded-lg px-4 py-3 text-sm font-medium text-gray-600 transition-colors duration-200 hover:bg-gray-50 hover:text-blue-600 dark:text-gray-400 dark:hover:bg-gray-900 dark:hover:text-blue-400"
                  >
                    <item.icon className="h-4 w-4" />
                    <span>{item.name}</span>
                  </Link>
                ))}

              {isAppShell && user && (
                <>
                  <Link
                    to="/app/profile"
                    onClick={() => setIsMobileMenuOpen(false)}
                    className="flex items-center space-x-3 rounded-lg px-4 py-3 text-sm font-medium text-gray-600 transition-colors duration-200 hover:bg-gray-50 hover:text-blue-600 dark:text-gray-400 dark:hover:bg-gray-900 dark:hover:text-blue-400"
                  >
                    <UserCircle2 className="h-4 w-4" />
                    <span>Profile</span>
                  </Link>
                  <button
                    onClick={() => {
                      setIsMobileMenuOpen(false);
                      handleLogout();
                    }}
                    className="flex items-center space-x-3 rounded-lg px-4 py-3 text-left text-sm font-medium text-gray-600 transition-colors duration-200 hover:bg-gray-50 hover:text-blue-600 dark:text-gray-400 dark:hover:bg-gray-900 dark:hover:text-blue-400"
                  >
                    <LogOut className="h-4 w-4" />
                    <span>Log out</span>
                  </button>
                </>
              )}

              {isAppShell && (
                <div className="border-t border-gray-100 pt-3 dark:border-gray-800">
                  <ThemeToggle />
                </div>
              )}
            </nav>
          </div>
        </div>
      )}
    </header>
  );
};

export default Header;
