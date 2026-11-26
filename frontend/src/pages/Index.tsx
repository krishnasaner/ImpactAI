import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import Footer from '@/components/layout/Footer';
import {
  MessageCircle,
  Shield,
  Heart,
  CheckCircle,
  Zap,
  Star,
  ChevronDown,
  ArrowRight,
  Sparkles,
  Users,
  Lock,
  Clock,
  Menu,
  X,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import PageTransition from '@/components/ui/PageTransition';
import ScrollFadeIn from '@/components/ui/ScrollFadeIn';

// FAQ Item Component
interface FAQItemProps {
  question: string;
  answer: string;
  isOpen: boolean;
  onClick: () => void;
}

const FAQItem = ({ question, answer, isOpen, onClick }: FAQItemProps) => {
  return (
    <div
      className={`border rounded-xl transition-all duration-300 ${
        isOpen
          ? 'border-[#2F7A6D]/30 bg-teal-50'
          : 'border-gray-100 bg-white'
      }`}
    >
      <button
        onClick={onClick}
        className="w-full p-6 text-left flex justify-between items-center group"
      >
        <span className="font-medium text-lg text-gray-800 group-hover:text-[#2F7A6D] transition-colors pr-4">
          {question}
        </span>
        <ChevronDown
          className={`h-5 w-5 text-gray-400 transition-transform duration-300 flex-shrink-0 ${
            isOpen ? 'rotate-180 text-[#2F7A6D]' : ''
          }`}
        />
      </button>

      <div
        className={`overflow-hidden transition-all duration-300 ease-in-out ${
          isOpen ? 'max-h-40 px-6 pb-6 opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="text-gray-600 leading-relaxed">{answer}</div>
      </div>
    </div>
  );
};

const Index = () => {
  const [activeTestimonial, setActiveTestimonial] = useState(0);
  const [openIndex, setOpenIndex] = useState<number | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const testimonials = [
    {
      name: 'Anonymous',
      role: 'Computer Science Student',
      content:
        'Impact AI helped me through my toughest semester. The AI chat was there when I needed it most at 3 AM during finals week.',
      rating: 5,
    },
    {
      name: 'Anonymous',
      role: 'Psychology Major',
      content:
        'The counseling sessions are incredibly professional and confidential. It removed the stigma I felt about seeking help.',
      rating: 5,
    },
    {
      name: 'Anonymous',
      role: 'Engineering Student',
      content:
        "The peer support forum connected me with others who understood what I was going through. I'm not alone anymore.",
      rating: 5,
    },
  ];

  const faqs = [
    {
      question: 'Is Impact AI completely confidential?',
      answer:
        'Absolutely. We adhere to strict HIPAA compliance standards. Your conversations are completely confidential.',
    },
    {
      question: 'How does the AI crisis detection work?',
      answer:
        'Our AI uses validated screening tools like PHQ-9 and GAD-7 to assess your responses. Crisis indicators connect you with emergency resources immediately.',
    },
    {
      question: 'Are the counselors real licensed professionals?',
      answer: 'Yes, all our counselors are licensed mental health professionals.',
    },
    {
      question: 'Is Impact AI free for students?',
      answer:
        'We offer a comprehensive free tier with AI chat, basic resources, and forum access. Premium counseling may have costs but are often discounted for students.',
    },
    {
      question: 'Can I remain anonymous on the platform?',
      answer:
        'Yes, especially in our peer support forums. Basic info is collected for safety, but participation can be anonymous.',
    },
    {
      question: 'What if I am having a mental health emergency?',
      answer:
        'If you are in immediate danger, call 112. For mental health support in India, you can call Tele-MANAS at 14416 or use the in-app crisis resources.',
    },
  ];

  const features = [
    {
      icon: <Lock className="h-6 w-6 text-[#2F7A6D]" />,
      title: 'End-to-End Privacy',
      desc: 'HIPAA-compliant security ensures your conversations and data remain completely confidential.',
    },
    {
      icon: <MessageCircle className="h-6 w-6 text-[#2F7A6D]" />,
      title: '24/7 AI Support',
      desc: 'An empathetic AI companion available around the clock — whenever you need someone to talk to.',
    },
    {
      icon: <Shield className="h-6 w-6 text-[#2F7A6D]" />,
      title: 'Smart Crisis Detection',
      desc: 'AI-powered screening tools detect distress signals and connect you with emergency resources instantly.',
    },
    {
      icon: <Users className="h-6 w-6 text-[#2F7A6D]" />,
      title: 'Peer Community',
      desc: 'Join anonymous peer forums to share, listen, and heal together with students who understand.',
    },
    {
      icon: <Heart className="h-6 w-6 text-[#2F7A6D]" />,
      title: 'Licensed Counselors',
      desc: 'Book confidential sessions with real, licensed mental health professionals at discounted rates.',
    },
    {
      icon: <Clock className="h-6 w-6 text-[#2F7A6D]" />,
      title: 'Always Available',
      desc: 'Resources, tools, and support accessible anytime — at 3 AM during finals or a Saturday morning.',
    },
  ];

  const steps = [
    {
      num: '1',
      title: 'Create your account',
      desc: 'Sign up in seconds — no credit card required. Your privacy is protected from day one.',
    },
    {
      num: '2',
      title: 'Chat with Zenith',
      desc: 'Start a conversation with our empathetic AI companion. It listens, understands, and guides.',
    },
    {
      num: '3',
      title: 'Access real support',
      desc: 'Get connected to peer forums, licensed counselors, or crisis resources whenever you need.',
    },
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveTestimonial((prev: number) => (prev + 1) % testimonials.length);
    }, 4000);
    return () => clearInterval(timer);
  }, [testimonials.length]);

  return (
    <PageTransition>
      {/* ── Navigation Header ── */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur border-b border-gray-100">
        <div className="container flex h-16 items-center justify-between px-6 mx-auto">
          {/* Logo */}
          <Link to="/" className="flex items-center shrink-0 hover:opacity-80 transition-opacity">
            <img src="/ImpactAI_logo.png" alt="Impact AI" className="h-11 md:h-12 w-auto max-w-[170px] object-contain" />
          </Link>

          {/* Desktop nav links */}
          <nav className="hidden md:flex items-center space-x-8 text-sm font-medium">
            <Link to="/about" className="text-gray-600 hover:text-[#2F7A6D] transition-colors">
              About
            </Link>
            <Link to="/app/resources" className="text-gray-600 hover:text-[#2F7A6D] transition-colors">
              Resources
            </Link>
            <Link to="/app/forum" className="text-gray-600 hover:text-[#2F7A6D] transition-colors">
              Community
            </Link>
          </nav>

          {/* Desktop CTA */}
          <div className="hidden md:flex items-center gap-3">
            <Button
              asChild
              className="bg-[#2F7A6D] hover:bg-[#256358] text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition-all duration-200"
            >
              <Link to="/login">Get Started</Link>
            </Button>
          </div>

          {/* Mobile hamburger */}
          <button
            className="md:hidden p-2 text-gray-600 hover:text-[#2F7A6D] transition-colors"
            onClick={() => setMobileMenuOpen((v: boolean) => !v)}
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-white border-t border-gray-100 px-6 py-4 space-y-3">
            <Link
              to="/about"
              className="block text-gray-700 hover:text-[#2F7A6D] font-medium py-1 transition-colors"
              onClick={() => setMobileMenuOpen(false)}
            >
              About
            </Link>
            <Link
              to="/app/resources"
              className="block text-gray-700 hover:text-[#2F7A6D] font-medium py-1 transition-colors"
              onClick={() => setMobileMenuOpen(false)}
            >
              Resources
            </Link>
            <Link
              to="/app/forum"
              className="block text-gray-700 hover:text-[#2F7A6D] font-medium py-1 transition-colors"
              onClick={() => setMobileMenuOpen(false)}
            >
              Community
            </Link>
            <Button
              asChild
              className="w-full bg-[#2F7A6D] hover:bg-[#256358] text-white font-semibold rounded-lg mt-2"
            >
              <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
                Get Started
              </Link>
            </Button>
          </div>
        )}
      </header>

      {/* ── Hero Section ── */}
      <ScrollFadeIn yOffset={30} delay={0.03}>
        <section className="relative bg-gradient-to-br from-teal-50 via-white to-blue-50 pt-32 pb-24 sm:pt-40 sm:pb-32 overflow-hidden min-h-screen flex items-center justify-center">
          <div className="relative z-10 container mx-auto px-6 text-center">
            {/* Logo badge */}
            <div className="mb-8 flex justify-center">
              <div className="rounded-2xl border border-gray-100 bg-white px-5 py-3 shadow-lg">
                <img
                  src="/ImpactAI_logo.png"
                  alt="Impact AI"
                  className="h-16 md:h-20 w-auto object-contain"
                />
              </div>
            </div>

            {/* Trust badge */}
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-teal-50 text-[#2F7A6D] border border-teal-200 text-sm font-medium mb-8">
              <Sparkles className="h-4 w-4" />
              Trusted by 10,000+ Students
            </div>

            {/* Main headline */}
            <h1 className="text-5xl sm:text-6xl md:text-7xl font-extrabold text-gray-900 leading-[1.08] tracking-tight mb-6">
              Your mental wellness{' '}
              <br className="hidden sm:block" />
              <span className="text-[#2F7A6D]">companion</span>
            </h1>

            {/* Subtext */}
            <p className="text-lg sm:text-xl text-gray-600 max-w-2xl mx-auto mb-12 leading-relaxed">
              Meet <strong className="text-[#2F7A6D]">Zenith</strong> — your always-on AI companion that
              listens without judgement. Navigate challenges, build resilience, and find the right support,
              anytime.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center motion-reduce:transition-none">
              <Button
                size="lg"
                className="bg-[#FFB400] hover:bg-amber-500 text-black font-semibold h-14 px-8 rounded-full shadow-md transition-all duration-300 motion-reduce:transition-none"
                asChild
              >
                <Link to="/signup">Get Started Free</Link>
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="border-2 border-[#2F7A6D] text-[#2F7A6D] hover:bg-teal-50 font-medium h-14 px-8 rounded-full transition-all duration-300 motion-reduce:transition-none"
                asChild
              >
                <Link to="/about">Learn More</Link>
              </Button>
            </div>
          </div>
        </section>
      </ScrollFadeIn>

      {/* ── Features Section ── */}
      <ScrollFadeIn yOffset={24} delay={0.08}>
        <section className="py-20 sm:py-28 px-6 bg-gray-50">
          <div className="container mx-auto max-w-5xl">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                Built for Trust &amp; Safety
              </h2>
              <p className="text-lg text-gray-500 max-w-xl mx-auto">
                Every feature is designed with your privacy, security, and wellbeing at the center.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {features.map((feature, i) => (
                <div
                  key={i}
                  className="bg-white border border-gray-100 rounded-xl p-6 shadow-md hover:-translate-y-0.5 transition-transform duration-300 motion-reduce:transform-none"
                >
                  <div className="w-12 h-12 rounded-xl bg-teal-50 flex items-center justify-center mb-4">
                    {feature.icon}
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
                  <p className="text-gray-500 leading-relaxed text-sm">{feature.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </ScrollFadeIn>

      {/* ── How It Works ── */}
      <ScrollFadeIn yOffset={24} delay={0.1}>
        <section className="py-20 sm:py-28 px-6 bg-white">
          <div className="container mx-auto max-w-4xl">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">How It Works</h2>
              <p className="text-lg text-gray-500">Start your wellness journey in three simple steps.</p>
            </div>

            <div className="relative flex flex-col md:flex-row items-start md:items-center gap-8 md:gap-0">
              {steps.map((step, i) => (
                <div key={i} className="flex-1 flex flex-col items-center text-center relative">
                  {/* Dashed connector line between steps */}
                  {i < steps.length - 1 && (
                    <div className="hidden md:block absolute top-6 left-[55%] w-full border-t-2 border-dashed border-gray-200 z-0" />
                  )}
                  <div className="relative z-10 w-12 h-12 rounded-full bg-[#2F7A6D] text-white flex items-center justify-center font-bold text-lg shadow-md mb-4">
                    {step.num}
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{step.title}</h3>
                  <p className="text-gray-500 text-sm leading-relaxed max-w-[200px]">{step.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </ScrollFadeIn>

      {/* ── Zenith Introduction ── */}
      <ScrollFadeIn yOffset={24} delay={0.11}>
        <section className="py-20 sm:py-28 px-6 bg-teal-50">
          <div className="container mx-auto max-w-4xl">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                Meet <span className="text-[#2F7A6D]">Zenith</span>
              </h2>
              <p className="text-lg text-gray-500 max-w-xl mx-auto">
                Your empathetic AI companion. Available anytime, free from judgement, always listening.
              </p>
            </div>

            {/* Chat mockup */}
            <div className="bg-white rounded-2xl shadow-md p-6 max-w-lg mx-auto border border-gray-100">
              <div className="flex items-center gap-3 mb-5 pb-4 border-b border-gray-100">
                <div className="w-9 h-9 rounded-full bg-[#2F7A6D] flex items-center justify-center">
                  <Sparkles className="h-4 w-4 text-white" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900 text-sm">Zenith</p>
                  <p className="text-xs text-green-500 font-medium">● Online</p>
                </div>
              </div>

              {/* Messages */}
              <div className="space-y-3">
                <div className="flex justify-start">
                  <div className="bg-teal-50 text-gray-700 rounded-2xl rounded-tl-sm px-4 py-2.5 text-sm max-w-[80%]">
                    Hi! I'm Zenith. How are you feeling today? 😊
                  </div>
                </div>
                <div className="flex justify-end">
                  <div className="bg-[#2F7A6D] text-white rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm max-w-[80%]">
                    I've been really stressed about exams...
                  </div>
                </div>
                <div className="flex justify-start">
                  <div className="bg-teal-50 text-gray-700 rounded-2xl rounded-tl-sm px-4 py-2.5 text-sm max-w-[80%]">
                    That sounds tough. Let's talk through it together — you don't have to face this alone. 💙
                  </div>
                </div>
              </div>

              <div className="mt-5 flex gap-2">
                <input
                  type="text"
                  placeholder="Type a message..."
                  className="flex-1 border border-gray-200 rounded-full px-4 py-2 text-sm focus:outline-none focus:border-[#2F7A6D] transition-colors bg-gray-50"
                  readOnly
                />
                <button className="w-9 h-9 rounded-full bg-[#2F7A6D] flex items-center justify-center hover:bg-[#256358] transition-colors">
                  <ArrowRight className="h-4 w-4 text-white" />
                </button>
              </div>
            </div>
          </div>
        </section>
      </ScrollFadeIn>

      {/* ── Testimonials ── */}
      <ScrollFadeIn yOffset={24} delay={0.12}>
        <section className="py-20 sm:py-28 px-6 bg-teal-50">
          <div className="container mx-auto max-w-3xl text-center">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Real Stories, Real Impact
            </h2>
            <p className="text-lg text-gray-500 mb-16">
              Hear from students who found the support they needed.
            </p>

            <div className="relative min-h-[200px]">
              {testimonials.map((testimonial, index) => (
                <div
                  key={index}
                  className={`transition-all duration-700 motion-reduce:transition-none ${
                    index === activeTestimonial
                      ? 'opacity-100 translate-y-0'
                      : 'opacity-0 absolute inset-0 translate-y-4'
                  }`}
                >
                  <div className="bg-white rounded-2xl shadow-md p-8 border border-gray-100">
                    <div className="flex items-center justify-center gap-1 mb-4">
                      {Array.from({ length: testimonial.rating }).map((_, i) => (
                        <Star key={i} className="h-4 w-4 fill-amber-400 text-amber-400" />
                      ))}
                    </div>
                    <blockquote className="text-xl text-gray-700 leading-relaxed font-light italic mb-6">
                      "{testimonial.content}"
                    </blockquote>
                    <p className="text-sm text-gray-500 font-medium">
                      {testimonial.name} · {testimonial.role}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {/* Dot indicators */}
            <div className="flex justify-center gap-2 mt-10">
              {testimonials.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setActiveTestimonial(index)}
                  className={`h-2 rounded-full transition-all duration-300 motion-reduce:transition-none ${
                    index === activeTestimonial
                      ? 'bg-[#2F7A6D] w-6'
                      : 'w-2 bg-gray-300 hover:bg-gray-400'
                  }`}
                />
              ))}
            </div>
          </div>
        </section>
      </ScrollFadeIn>

      {/* ── Stats Strip ── */}
      <ScrollFadeIn yOffset={20} delay={0.14}>
        <section className="py-16 px-6 bg-[#2F7A6D]">
          <div className="container mx-auto max-w-4xl">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
              <div>
                <div className="text-3xl md:text-4xl font-bold text-white">10K+</div>
                <div className="text-sm text-teal-100 mt-1">Active Students</div>
              </div>
              <div>
                <div className="text-3xl md:text-4xl font-bold text-white">24/7</div>
                <div className="text-sm text-teal-100 mt-1">AI Availability</div>
              </div>
              <div>
                <div className="text-3xl md:text-4xl font-bold text-white">98%</div>
                <div className="text-sm text-teal-100 mt-1">Satisfaction Rate</div>
              </div>
              <div>
                <div className="text-3xl md:text-4xl font-bold text-white">100%</div>
                <div className="text-sm text-teal-100 mt-1">Confidential</div>
              </div>
            </div>
          </div>
        </section>
      </ScrollFadeIn>

      {/* ── FAQs ── */}
      <ScrollFadeIn yOffset={24} delay={0.16}>
        <section className="py-20 sm:py-28 px-6 bg-white">
          <div className="container mx-auto max-w-3xl">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                Frequently Asked Questions
              </h2>
              <p className="text-lg text-gray-500">Everything you need to know about Impact AI.</p>
            </div>

            <div className="space-y-3">
              {faqs.map((faq, index) => (
                <FAQItem
                  key={index}
                  question={faq.question}
                  answer={faq.answer}
                  isOpen={openIndex === index}
                  onClick={() => setOpenIndex(openIndex === index ? null : index)}
                />
              ))}
            </div>
          </div>
        </section>
      </ScrollFadeIn>

      {/* ── Final CTA ── */}
      <ScrollFadeIn yOffset={20} delay={0.18}>
        <section className="py-20 sm:py-28 px-6 bg-gradient-to-br from-teal-50 via-white to-blue-50 text-center">
          <div className="container mx-auto max-w-2xl">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Ready to prioritize your wellbeing?
            </h2>
            <p className="text-lg text-gray-500 mb-10">
              Join thousands of students who have taken the first step toward better mental health.
            </p>
            <Button
              size="lg"
              className="bg-[#FFB400] hover:bg-amber-500 text-black font-semibold h-14 px-10 rounded-full shadow-md transition-all duration-300 motion-reduce:transition-none"
              asChild
            >
              <Link to="/signup">
                Start Your Journey
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            </Button>
          </div>
        </section>
      </ScrollFadeIn>

      <Footer />
    </PageTransition>
  );
};

export default Index;
