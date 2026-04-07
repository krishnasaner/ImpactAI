import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';

import { ThemeToggle } from '@/components/ui/theme-toggle';
import QuickMoodHeader from '@/components/dashboard/QuickMoodHeader';
import {
  Menu,
  X,
  MessageCircle,
  Calendar,
  BookOpen,
  Users,
  Globe,
  BarChart,
  FileText,
  LucideIcon,
} from 'lucide-react';

type NavItem = {
  name: string;
  href: string;
  icon: LucideIcon;
};

const Header = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navItems: NavItem[] = [
    { name: 'Dashboard', href: '/app/dashboard', icon: BarChart },
    { name: 'Chat', href: '/app/chat', icon: MessageCircle },
    { name: 'Resources', href: '/app/resources', icon: BookOpen },
    { name: 'Forum', href: '/app/forum', icon: Users },
    { name: 'Blog', href: '/app/blog', icon: FileText },
    { name: 'About', href: '/about', icon: Globe },
  ];

  return (
    <header className="sticky top-0 z-50 w-full bg-white border-b border-gray-100 shadow-sm dark:bg-gray-950 dark:border-gray-800">
      <div className="container flex h-16 items-center justify-between px-6">
        {/* Logo */}
        <Link
          to="/"
          className="flex items-center shrink-0 group transition-all duration-300 hover:opacity-80"
        >
          <img
            src="/ImpactAI_logo.png"
            alt="Impact AI"
            className="h-9 w-auto object-contain"
          />
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden lg:flex items-center space-x-1 text-sm font-medium ml-10">
          {navItems.map((item) => (
            <Link
              key={item.name}
              to={item.href}
              className="px-3 py-2 rounded-lg text-gray-500 hover:text-blue-600 hover:bg-gray-50 transition-colors duration-200 dark:text-gray-400 dark:hover:text-blue-400 dark:hover:bg-gray-900"
            >
              <span>{item.name}</span>
            </Link>
          ))}
        </nav>

        <div className="flex items-center space-x-3">
          {/* Quick Mood Header */}
          <div className="hidden md:block">
            <QuickMoodHeader variant="dropdown" showTrend={false} />
          </div>

          {/* Theme Toggle */}
          <div className="hidden sm:block">
            <ThemeToggle />
          </div>

          {/* Mobile Menu Button */}
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden rounded-lg"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          >
            {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
        </div>
      </div>

      {/* Mobile Navigation */}
      {isMobileMenuOpen && (
        <div className="lg:hidden border-t border-gray-100 bg-white dark:bg-gray-950 dark:border-gray-800">
          <div className="container py-4 px-6">
            <nav className="flex flex-col space-y-1">
              {navItems.map((item) => (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium text-gray-600 hover:text-blue-600 hover:bg-gray-50 transition-colors duration-200 dark:text-gray-400 dark:hover:text-blue-400 dark:hover:bg-gray-900"
                >
                  <item.icon className="h-4 w-4" />
                  <span>{item.name}</span>
                </Link>
              ))}
              <div className="pt-3 border-t border-gray-100 dark:border-gray-800">
                <ThemeToggle />
              </div>
            </nav>
          </div>
        </div>
      )}
    </header>
  );
};

export default Header;
