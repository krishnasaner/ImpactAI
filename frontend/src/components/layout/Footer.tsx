import { Link } from 'react-router-dom';
import {
  Mail,
  Phone,
  MapPin,
  Facebook,
  Twitter,
  Instagram,
  Linkedin,
  Youtube,
  Shield,
  Lock,
  Users,
  MessageCircle,
  Calendar,
  BookOpen,
  Globe,
} from 'lucide-react';

const Footer = () => {
  const currentYear = new Date().getFullYear();

  const footerLinks = {
    platform: [
      { name: 'AI Chat Support', href: '/app/chat', icon: MessageCircle },
      { name: 'Book Session', href: '/app/booking', icon: Calendar },
      { name: 'Resources', href: '/app/resources', icon: BookOpen },
      { name: 'Community Forum', href: '/app/forum', icon: Users },
    ],
    company: [
      { name: 'About Us', href: '/about' },
      { name: 'Contact Us', href: '/contact' },
      { name: 'Privacy Policy', href: '/privacy' },
      { name: 'Terms of Service', href: '/terms' },
    ],
    support: [
      { name: 'Help Center', href: '/contact' },
      { name: 'Crisis Support', href: '/contact' },
      { name: 'FAQ', href: '/#faq' },
      { name: 'Report Issue', href: '/contact' },
    ],
  };

  const socialLinks = [
    { name: 'Facebook', href: 'https://facebook.com/impactai', icon: Facebook },
    { name: 'Twitter', href: 'https://twitter.com/impactai', icon: Twitter },
    { name: 'Instagram', href: 'https://instagram.com/impactai', icon: Instagram },
    { name: 'LinkedIn', href: 'https://linkedin.com/company/impactai', icon: Linkedin },
    { name: 'YouTube', href: 'https://youtube.com/impactai', icon: Youtube },
  ];

  return (
    <footer className="bg-slate-50 border-t border-gray-200 mt-auto text-gray-600">
      {/* Main Footer Content */}
      <div className="container mx-auto px-6 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Brand Section */}
          <div className="lg:col-span-1 space-y-4">
            <Link
              to="/"
              className="flex items-center group transition-all duration-300 hover:opacity-85"
            >
              <img src="/ImpactAI_logo.png" alt="Impact AI Logo" className="h-14 w-auto object-contain" />
            </Link>

            <p className="text-sm text-gray-500 leading-relaxed max-w-sm">
              Supporting students' mental health with AI-powered assistance, professional
              counseling, and a safe, stigma-free community environment.
            </p>

            {/* Trust Indicators */}
            <div className="flex items-center space-x-4 pt-2">
              <div className="flex items-center space-x-2 text-xs font-medium text-gray-600">
                <Shield className="h-4 w-4 text-[#2F7A6D]" />
                <span>Privacy notice</span>
              </div>
            </div>
          </div>

          {/* Platform Links */}
          <div className="space-y-4">
            <h3 className="font-semibold text-base text-gray-900">Platform</h3>
            <ul className="space-y-2.5 text-sm">
              {footerLinks.platform.map((link) => (
                <li key={link.name}>
                  <Link
                    to={link.href}
                    className="flex items-center space-x-2 text-gray-600 hover:text-[#2F7A6D] transition-colors group"
                  >
                    <link.icon className="h-4 w-4 text-gray-400 group-hover:text-[#2F7A6D] transition-colors" />
                    <span>{link.name}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Company Links */}
          <div className="space-y-4">
            <h3 className="font-semibold text-base text-gray-900">Company</h3>
            <ul className="space-y-2.5 text-sm">
              {footerLinks.company.map((link) => (
                <li key={link.name}>
                  <Link
                    to={link.href}
                    className="text-gray-600 hover:text-[#2F7A6D] transition-colors"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Support & Contact */}
          <div className="space-y-4">
            <h3 className="font-semibold text-base text-gray-900">Support</h3>
            <ul className="space-y-2.5 text-sm">
              {footerLinks.support.map((link) => (
                <li key={link.name}>
                  <Link
                    to={link.href}
                    className="text-gray-600 hover:text-[#2F7A6D] transition-colors"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>

            {/* Contact Information */}
            <div className="pt-2 space-y-2 text-sm text-gray-600">
              <div className="flex items-center space-x-2">
                <Mail className="h-4 w-4 text-[#2F7A6D]" />
                <a
                  href="mailto:support@impactai.com"
                  className="hover:text-[#2F7A6D] transition-colors"
                >
                  support@impactai.com
                </a>
              </div>
              <div className="flex items-center space-x-2">
                <Phone className="h-4 w-4 text-[#2F7A6D]" />
                <a href="tel:14416" className="hover:text-[#2F7A6D] transition-colors">
                  Helpline: 14416 (Tele-MANAS)
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* Social Media & Newsletter */}
        <div className="mt-10 pt-6 border-t border-gray-200">
          <div className="flex flex-col lg:flex-row justify-between items-center gap-6">
            {/* Social Media Links */}
            <div className="flex items-center space-x-4">
              <span className="text-sm font-medium text-gray-700">Follow us:</span>
              <div className="flex items-center space-x-2">
                {socialLinks.map((social) => (
                  <a
                    key={social.name}
                    href={social.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 rounded-lg bg-white border border-gray-200 text-gray-500 hover:text-[#2F7A6D] hover:border-[#2F7A6D] transition-colors"
                    aria-label={`Follow us on ${social.name}`}
                  >
                    <social.icon className="h-4 w-4" />
                  </a>
                ))}
              </div>
            </div>

            {/* Newsletter Signup */}
            <div className="flex items-center space-x-3">
              <span className="text-sm font-medium text-gray-700 hidden sm:inline">Stay updated:</span>
              <form onSubmit={(e) => e.preventDefault()} className="flex items-center space-x-2">
                <input
                  type="email"
                  placeholder="Enter your email"
                  className="px-3.5 py-2 text-sm bg-white border border-gray-200 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#2F7A6D]/20 focus:border-[#2F7A6D] transition-colors"
                />
                <button
                  type="submit"
                  className="px-4 py-2 text-sm bg-[#2F7A6D] hover:bg-teal-700 text-white font-medium rounded-lg transition-colors"
                >
                  Subscribe
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="border-t border-gray-200 bg-gray-100/70">
        <div className="container mx-auto px-6 py-4">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-gray-500">
            {/* Copyright */}
            <div>
              <span>© {currentYear} ImpactAI. All rights reserved.</span>
            </div>

            {/* Additional Links */}
            <div className="flex items-center space-x-6">
              <Link to="/privacy" className="hover:text-[#2F7A6D] transition-colors">
                Privacy Policy
              </Link>
              <Link to="/terms" className="hover:text-[#2F7A6D] transition-colors">
                Terms of Service
              </Link>
              <Link to="/cookies" className="hover:text-[#2F7A6D] transition-colors">
                Cookie Policy
              </Link>
            </div>

            {/* Crisis Support Notice */}
            <div className="flex items-center space-x-1.5 text-gray-600">
              <Globe className="h-3.5 w-3.5 text-[#2F7A6D]" />
              <span>Available 24/7 for student wellness</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
