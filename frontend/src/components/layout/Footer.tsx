import { Link } from 'react-router-dom';
import {
  Heart,
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
      { name: 'Help Center', href: '/help' },
      { name: 'Crisis Support', href: '/crisis' },
      { name: 'FAQ', href: '/faq' },
      { name: 'Report Issue', href: '/report' },
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
    <footer className="bg-[#071A1F] border-t border-[#4FD1C5]/[0.08] mt-auto text-[#F8FAFC]/70">
      {/* Main Footer Content */}
      <div className="container mx-auto px-6 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Brand Section */}
          <div className="lg:col-span-1 space-y-4">
            <Link
              to="/"
              className="flex items-center group transition-all duration-300 hover:scale-105"
            >
              <img src="/ImpactAI_logo.png" alt="Impact AI Logo" className="h-16 md:h-20 w-auto object-contain" />
            </Link>

            <p className="leading-relaxed max-w-sm">
              Supporting students' mental health with AI-powered assistance, professional
              counseling, and a safe community environment.
            </p>

            {/* Trust Indicators */}
            <div className="flex items-center space-x-4 pt-2">
              <div className="flex items-center space-x-2 text-sm text-[#F8FAFC]/70">
                <Shield className="h-4 w-4 text-[#4FD1C5]" />
                <span>HIPAA Compliant</span>
              </div>
              <div className="flex items-center space-x-2 text-sm text-[#F8FAFC]/70">
                <Lock className="h-4 w-4 text-[#4FD1C5]" />
                <span>Secure</span>
              </div>
            </div>
          </div>

          {/* Platform Links */}
          <div className="space-y-4">
            <h3 className="font-semibold text-lg text-[#F8FAFC]">Platform</h3>
            <ul className="space-y-3">
              {footerLinks.platform.map((link) => (
                <li key={link.name}>
                  <Link
                    to={link.href}
                    className="flex items-center space-x-2 text-[#F8FAFC]/70 hover:text-[#4FD1C5] gentle-transition group"
                  >
                    <link.icon className="h-4 w-4 group-hover:scale-110 transition-transform duration-200" />
                    <span>{link.name}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Company Links */}
          <div className="space-y-4">
            <h3 className="font-semibold text-lg text-[#F8FAFC]">Company</h3>
            <ul className="space-y-3">
              {footerLinks.company.map((link) => (
                <li key={link.name}>
                  <Link
                    to={link.href}
                    className="text-[#F8FAFC]/70 hover:text-[#4FD1C5] gentle-transition"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Support & Contact */}
          <div className="space-y-4">
            <h3 className="font-semibold text-lg text-[#F8FAFC]">Support</h3>
            <ul className="space-y-3">
              {footerLinks.support.map((link) => (
                <li key={link.name}>
                  <Link
                    to={link.href}
                    className="text-[#F8FAFC]/70 hover:text-[#4FD1C5] gentle-transition"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>

            {/* Contact Information */}
            <div className="pt-4 space-y-2">
              <div className="flex items-center space-x-2 text-sm text-[#F8FAFC]/70">
                <Mail className="h-4 w-4" />
                <a
                  href="mailto:support@impactai.com"
                  className="hover:text-[#4FD1C5] gentle-transition"
                >
                  support@impactai.com
                </a>
              </div>
              <div className="flex items-center space-x-2 text-sm text-[#F8FAFC]/70">
                <Phone className="h-4 w-4" />
                <a href="tel:+1234567890" className="hover:text-[#4FD1C5] gentle-transition">
                  +1 (234) 567-890
                </a>
              </div>
              <div className="flex items-center space-x-2 text-sm text-[#F8FAFC]/70">
                <MapPin className="h-4 w-4" />
                <span>San Francisco, CA</span>
              </div>
            </div>
          </div>
        </div>

        {/* Social Media & Newsletter */}
        <div className="mt-12 pt-8 border-t border-[#4FD1C5]/[0.08]">
          <div className="flex flex-col lg:flex-row justify-between items-center space-y-6 lg:space-y-0">
            {/* Social Media Links */}
            <div className="flex items-center space-x-4">
              <span className="text-sm font-medium text-[#F8FAFC]">Follow us:</span>
              <div className="flex items-center space-x-3">
                {socialLinks.map((social) => (
                  <a
                    key={social.name}
                    href={social.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 rounded-lg bg-white/5 hover:bg-[#4FD1C5]/10 hover:text-[#4FD1C5] gentle-transition group"
                    aria-label={`Follow us on ${social.name}`}
                  >
                    <social.icon className="h-5 w-5 group-hover:scale-110 transition-transform duration-200" />
                  </a>
                ))}
              </div>
            </div>

            {/* Newsletter Signup */}
            <div className="flex items-center space-x-4">
              <span className="text-sm font-medium text-[#F8FAFC]">Stay updated:</span>
              <div className="flex items-center space-x-2">
                <input
                  type="email"
                  placeholder="Enter your email"
                  className="px-3 py-2 text-sm bg-white/5 border border-[#4FD1C5]/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-[#4FD1C5]/20 focus:border-[#4FD1C5] gentle-transition"
                />
                <button className="px-4 py-2 text-sm bg-[#4FD1C5] hover:bg-[#38b2ac] text-[#071A1F] font-semibold rounded-lg gentle-transition">
                  Subscribe
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="border-t border-[#4FD1C5]/[0.08] bg-[#0E3440]/15">
        <div className="container mx-auto px-6 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            {/* Copyright */}
            <div className="flex items-center space-x-2 text-sm text-[#F8FAFC]/60">
              <span>© {currentYear} Impact AI. All rights reserved.</span>
            </div>

            {/* Additional Links */}
            <div className="flex items-center space-x-6 text-sm">
              <Link
                to="/privacy"
                className="text-[#F8FAFC]/60 hover:text-[#4FD1C5] gentle-transition"
              >
                Privacy Policy
              </Link>
              <Link
                to="/terms"
                className="text-[#F8FAFC]/60 hover:text-[#4FD1C5] gentle-transition"
              >
                Terms of Service
              </Link>
              <Link
                to="/cookies"
                className="text-[#F8FAFC]/60 hover:text-[#4FD1C5] gentle-transition"
              >
                Cookie Policy
              </Link>
            </div>

            {/* Crisis Support Notice */}
            <div className="flex items-center space-x-2 text-sm text-[#F8FAFC]/60">
              <Globe className="h-4 w-4" />
              <span>Available 24/7 for crisis support</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
