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
    <div className={`border rounded-xl transition-all duration-300 ${isOpen ? 'border-blue-200 bg-blue-50/30 dark:border-blue-900 dark:bg-blue-950/20' : 'border-gray-100 bg-white dark:border-gray-800 dark:bg-gray-950'}`}>
      <button
        onClick={onClick}
        className="w-full p-6 text-left flex justify-between items-center group"
      >
        <span className="font-medium text-lg text-gray-900 dark:text-gray-100 pr-4">{question}</span>
        <ChevronDown
          className={`h-5 w-5 text-gray-400 transition-transform duration-300 flex-shrink-0 ${
            isOpen ? 'rotate-180 text-blue-600' : ''
          }`}
        />
      </button>

      <div
        className={`overflow-hidden transition-all duration-300 ease-in-out ${
          isOpen ? 'max-h-40 px-6 pb-6 opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="text-gray-500 dark:text-gray-400 leading-relaxed">{answer}</div>
      </div>
    </div>
  );
};

const Index = () => {
  const [activeTestimonial, setActiveTestimonial] = useState(0);
  const [openIndex, setOpenIndex] = useState<number | null>(null);

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

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveTestimonial((prev: number) => (prev + 1) % testimonials.length);
    }, 4000);
    return () => clearInterval(timer);
  }, [testimonials.length]);

  return (
    <PageTransition>
      {/* ── Landing Header ── */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-sm border-b border-gray-100 dark:bg-gray-950/95 dark:border-gray-800">
        <div className="container flex h-24 items-center justify-between px-6 mx-auto">
          <Link to="/" className="flex items-center shrink-0 hover:opacity-80 transition-opacity">
            <img src="/ImpactAI_logo.png" alt="Impact AI" className="h-16 md:h-20 w-auto object-contain drop-shadow-sm" />
          </Link>
          <nav className="hidden md:flex items-center space-x-8 text-sm font-medium text-gray-500">
            <Link to="/about" className="hover:text-blue-600 transition-colors">About</Link>
            <Link to="/app/resources" className="hover:text-blue-600 transition-colors">Resources</Link>
            <Link to="/app/forum" className="hover:text-blue-600 transition-colors">Community</Link>
          </nav>
          <Button
            asChild
            className="bg-gray-900 hover:bg-gray-800 text-white text-sm font-medium px-5 py-2 rounded-lg shadow-sm dark:bg-blue-600 dark:hover:bg-blue-700"
          >
            <Link to="/login">Get Started</Link>
          </Button>
        </div>
      </header>

      {/* ── Hero Section: Pure White, Typography-Focused ── */}
      <ScrollFadeIn yOffset={30} delay={0.03}>
        <section className="relative bg-white dark:bg-gray-950 pt-32 pb-24 sm:pt-40 sm:pb-32 overflow-hidden">
          {/* Subtle watermark: large "M" shapes from the logo as background art */}
          <div className="absolute inset-0 pointer-events-none overflow-hidden opacity-[0.03] dark:opacity-[0.05]">
            <svg className="absolute -top-20 -left-32 w-[600px] h-[600px] text-blue-600" viewBox="0 0 200 200" fill="currentColor">
              <path d="M40 160V40l40 80 40-80v120M120 160V40l40 80 40-80v120" stroke="currentColor" strokeWidth="8" fill="none"/>
            </svg>
            <svg className="absolute -bottom-20 -right-32 w-[500px] h-[500px] text-blue-400" viewBox="0 0 200 200" fill="currentColor">
              <path d="M40 160V40l40 80 40-80v120M120 160V40l40 80 40-80v120" stroke="currentColor" strokeWidth="8" fill="none"/>
            </svg>
          </div>

          <div className="relative z-10 container mx-auto px-6 text-center">
            <div className="mb-8 flex justify-center">
              <div className="rounded-[2rem] border border-blue-100 bg-white/90 px-6 py-4 shadow-xl shadow-blue-100/40 backdrop-blur dark:border-gray-800 dark:bg-gray-950/90 dark:shadow-blue-950/20">
                <img src="/ImpactAI_logo.png" alt="Impact AI" className="h-24 md:h-28 w-auto object-contain" />
              </div>
            </div>
            {/* Trust badge */}
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-blue-50 text-blue-600 text-sm font-medium mb-8 dark:bg-blue-950/40 dark:text-blue-400">
              <Sparkles className="h-4 w-4" />
              Trusted by 10,000+ Students
            </div>

            {/* Main headline */}
            <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-extrabold text-gray-950 dark:text-white leading-[1.05] tracking-tight mb-6">
              Your Mental Health{' '}
              <br className="hidden sm:block" />
              <span className="text-blue-600">Matters Most</span>
            </h1>

            {/* Subtext */}
            <p className="text-lg sm:text-xl text-gray-500 dark:text-gray-400 max-w-2xl mx-auto mb-12 leading-relaxed">
              A futuristic, intuitive platform designed to support your wellbeing.
              Navigate challenges with an empathetic AI and trusted resources.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                size="lg"
                className="bg-gradient-to-br from-blue-500 to-blue-700 text-white text-lg font-medium h-14 px-8 rounded-full shadow-lg shadow-blue-200/50 hover:shadow-blue-300/60 hover:scale-[1.02] transition-all duration-300 dark:shadow-blue-900/30"
                asChild
              >
                <Link to="/signup">Get Started Free</Link>
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="text-gray-950 dark:text-white text-lg font-medium h-14 px-8 rounded-full border-2 border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-900 transition-all duration-300"
                asChild
              >
                <Link to="/about">Explore Features</Link>
              </Button>
            </div>
          </div>
        </section>
      </ScrollFadeIn>

      {/* ── Feature Cards Section ── */}
      <ScrollFadeIn yOffset={24} delay={0.08}>
        <section className="py-20 sm:py-28 px-6 bg-gray-50/50 dark:bg-gray-900/50">
          <div className="container mx-auto max-w-5xl">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-950 dark:text-white mb-4">
                Built for Trust & Safety
              </h2>
              <p className="text-lg text-gray-500 dark:text-gray-400 max-w-xl mx-auto">
                Every feature is designed with your privacy, security, and wellbeing at the center.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Card 1: Privacy */}
              <div className="group bg-white dark:bg-gray-950 rounded-2xl border border-gray-100 dark:border-gray-800 p-8 hover:shadow-lg hover:shadow-blue-100/40 dark:hover:shadow-blue-950/20 transition-all duration-500 hover:-translate-y-1">
                <div className="w-12 h-12 rounded-xl bg-blue-50 dark:bg-blue-950/40 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                  <Lock className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">End-to-End Privacy</h3>
                <p className="text-gray-500 dark:text-gray-400 leading-relaxed">
                  HIPAA-compliant security ensures your conversations and data remain completely confidential.
                </p>
              </div>

              {/* Card 2: AI Support */}
              <div className="group bg-white dark:bg-gray-950 rounded-2xl border border-gray-100 dark:border-gray-800 p-8 hover:shadow-lg hover:shadow-blue-100/40 dark:hover:shadow-blue-950/20 transition-all duration-500 hover:-translate-y-1">
                <div className="w-12 h-12 rounded-xl bg-cyan-50 dark:bg-cyan-950/40 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                  <MessageCircle className="h-6 w-6 text-cyan-600 dark:text-cyan-400" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">24/7 AI Support</h3>
                <p className="text-gray-500 dark:text-gray-400 leading-relaxed">
                  An empathetic AI companion available around the clock — whenever you need someone to talk to.
                </p>
              </div>

              {/* Card 3: Crisis Detection */}
              <div className="group bg-white dark:bg-gray-950 rounded-2xl border border-gray-100 dark:border-gray-800 p-8 hover:shadow-lg hover:shadow-blue-100/40 dark:hover:shadow-blue-950/20 transition-all duration-500 hover:-translate-y-1">
                <div className="w-12 h-12 rounded-xl bg-amber-50 dark:bg-amber-950/40 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                  <Shield className="h-6 w-6 text-amber-600 dark:text-amber-400" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">Smart Crisis Detection</h3>
                <p className="text-gray-500 dark:text-gray-400 leading-relaxed">
                  AI-powered screening tools detect distress signals and connect you with emergency resources instantly.
                </p>
              </div>

              {/* Card 4: Community */}
              <div className="group bg-white dark:bg-gray-950 rounded-2xl border border-gray-100 dark:border-gray-800 p-8 hover:shadow-lg hover:shadow-blue-100/40 dark:hover:shadow-blue-950/20 transition-all duration-500 hover:-translate-y-1">
                <div className="w-12 h-12 rounded-xl bg-green-50 dark:bg-green-950/40 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                  <Users className="h-6 w-6 text-green-600 dark:text-green-400" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">Peer Community</h3>
                <p className="text-gray-500 dark:text-gray-400 leading-relaxed">
                  Join anonymous peer forums to share, listen, and heal together with students who understand.
                </p>
              </div>

              {/* Card 5: Professional Counseling */}
              <div className="group bg-white dark:bg-gray-950 rounded-2xl border border-gray-100 dark:border-gray-800 p-8 hover:shadow-lg hover:shadow-blue-100/40 dark:hover:shadow-blue-950/20 transition-all duration-500 hover:-translate-y-1">
                <div className="w-12 h-12 rounded-xl bg-purple-50 dark:bg-purple-950/40 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                  <Heart className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">Licensed Counselors</h3>
                <p className="text-gray-500 dark:text-gray-400 leading-relaxed">
                  Book confidential sessions with real, licensed mental health professionals at discounted rates.
                </p>
              </div>

              {/* Card 6: Always Available */}
              <div className="group bg-white dark:bg-gray-950 rounded-2xl border border-gray-100 dark:border-gray-800 p-8 hover:shadow-lg hover:shadow-blue-100/40 dark:hover:shadow-blue-950/20 transition-all duration-500 hover:-translate-y-1">
                <div className="w-12 h-12 rounded-xl bg-rose-50 dark:bg-rose-950/40 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                  <Clock className="h-6 w-6 text-rose-600 dark:text-rose-400" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">Always Available</h3>
                <p className="text-gray-500 dark:text-gray-400 leading-relaxed">
                  Resources, tools, and support accessible anytime — at 3 AM during finals or a Saturday morning.
                </p>
              </div>
            </div>
          </div>
        </section>
      </ScrollFadeIn>

      {/* ── Social Proof / Testimonials ── */}
      <ScrollFadeIn yOffset={24} delay={0.12}>
        <section className="py-20 sm:py-28 px-6 bg-white dark:bg-gray-950">
          <div className="container mx-auto max-w-3xl text-center">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-950 dark:text-white mb-4">
              Real Stories, Real Impact
            </h2>
            <p className="text-lg text-gray-500 dark:text-gray-400 mb-16">
              Hear from students who found the support they needed.
            </p>

            <div className="relative">
              {testimonials.map((testimonial, index) => (
                <div
                  key={index}
                  className={`transition-all duration-700 ${
                    index === activeTestimonial
                      ? 'opacity-100 translate-y-0'
                      : 'opacity-0 absolute inset-0 translate-y-4'
                  }`}
                >
                  <blockquote className="text-xl sm:text-2xl text-gray-700 dark:text-gray-300 leading-relaxed font-light italic mb-8">
                    "{testimonial.content}"
                  </blockquote>
                  <div className="flex items-center justify-center gap-1 mb-3">
                    {Array.from({ length: testimonial.rating }).map((_, i) => (
                      <Star key={i} className="h-4 w-4 fill-amber-400 text-amber-400" />
                    ))}
                  </div>
                  <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">
                    {testimonial.name} · {testimonial.role}
                  </p>
                </div>
              ))}
            </div>

            {/* Dot indicators */}
            <div className="flex justify-center gap-2 mt-10">
              {testimonials.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setActiveTestimonial(index)}
                  className={`w-2 h-2 rounded-full transition-all duration-300 ${
                    index === activeTestimonial
                      ? 'bg-blue-600 w-6'
                      : 'bg-gray-300 dark:bg-gray-700 hover:bg-gray-400'
                  }`}
                />
              ))}
            </div>
          </div>
        </section>
      </ScrollFadeIn>

      {/* ── Stats Strip ── */}
      <ScrollFadeIn yOffset={20} delay={0.14}>
        <section className="py-16 px-6 bg-gray-50/50 dark:bg-gray-900/50 border-y border-gray-100 dark:border-gray-800">
          <div className="container mx-auto max-w-4xl">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
              <div>
                <div className="text-3xl md:text-4xl font-bold text-gray-950 dark:text-white">10K+</div>
                <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">Active Students</div>
              </div>
              <div>
                <div className="text-3xl md:text-4xl font-bold text-gray-950 dark:text-white">24/7</div>
                <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">AI Availability</div>
              </div>
              <div>
                <div className="text-3xl md:text-4xl font-bold text-gray-950 dark:text-white">98%</div>
                <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">Satisfaction Rate</div>
              </div>
              <div>
                <div className="text-3xl md:text-4xl font-bold text-gray-950 dark:text-white">100%</div>
                <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">Confidential</div>
              </div>
            </div>
          </div>
        </section>
      </ScrollFadeIn>

      {/* ── FAQs ── */}
      <ScrollFadeIn yOffset={24} delay={0.16}>
        <section className="py-20 sm:py-28 px-6 bg-white dark:bg-gray-950">
          <div className="container mx-auto max-w-3xl">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-950 dark:text-white mb-4">
                Frequently Asked Questions
              </h2>
              <p className="text-lg text-gray-500 dark:text-gray-400">
                Everything you need to know about Impact AI.
              </p>
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
        <section className="py-20 sm:py-28 px-6 bg-gray-950 dark:bg-gray-900 text-center">
          <div className="container mx-auto max-w-2xl">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Ready to prioritize your wellbeing?
            </h2>
            <p className="text-lg text-gray-400 mb-10">
              Join thousands of students who have taken the first step toward better mental health.
            </p>
            <Button
              size="lg"
              className="bg-blue-600 hover:bg-blue-700 text-white text-lg font-medium h-14 px-10 rounded-full shadow-lg shadow-blue-600/25 hover:shadow-blue-600/40 transition-all duration-300"
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
