import React from 'react';
import { Link } from 'react-router-dom';
import Header from '@/components/layout/Header';
import Footer from '@/components/layout/Footer';
import PageTransition from '@/components/ui/PageTransition';
import ScrollFadeIn from '@/components/ui/ScrollFadeIn';
import { Shield, Lock, Eye, CheckCircle2, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function PrivacyPolicy() {
  return (
    <PageTransition>
      <div className="min-h-screen bg-[#071A1F] text-[#F8FAFC]">
        <Header />
        <div className="h-20" />

        <main className="container mx-auto px-6 py-12 max-w-4xl">
          <ScrollFadeIn yOffset={20}>
            <div className="mb-8">
              <Button asChild variant="ghost" className="text-[#4FD1C5] hover:bg-[#4FD1C5]/10 mb-4 -ml-4">
                <Link to="/" className="inline-flex items-center gap-2">
                  <ArrowLeft className="h-4 w-4" />
                  Back to Home
                </Link>
              </Button>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#4FD1C5]/10 text-[#4FD1C5] text-xs font-semibold mb-3">
                <Shield className="h-3.5 w-3.5" />
                Your Privacy Matters
              </div>
              <h1 className="text-3xl md:text-5xl font-bold mb-4 tracking-tight">Privacy Policy</h1>
              <p className="text-[#F8FAFC]/70 text-base md:text-lg">
                Last updated: July 2026. Learn how ImpactAI protects your personal data, confidentiality, and wellbeing.
              </p>
            </div>

            <div className="space-y-8 bg-[#0E3440]/30 border border-[#4FD1C5]/10 rounded-2xl p-6 md:p-10 backdrop-blur-sm">
              <section className="space-y-3">
                <h2 className="text-xl md:text-2xl font-semibold text-[#4FD1C5] flex items-center gap-2">
                  <Lock className="h-5 w-5" /> 1. Commitment to Confidentiality
                </h2>
                <p className="text-[#F8FAFC]/80 leading-relaxed">
                  ImpactAI is built specifically for student mental wellness. We adhere to industry-standard HIPAA and FERPA best practices. All interactions with our AI companion, licensed counselors, and mood check-ins are encrypted in transit and at rest.
                </p>
              </section>

              <section className="space-y-3">
                <h2 className="text-xl md:text-2xl font-semibold text-[#4FD1C5] flex items-center gap-2">
                  <Eye className="h-5 w-5" /> 2. Information We Collect
                </h2>
                <ul className="list-disc list-inside space-y-2 text-[#F8FAFC]/80 leading-relaxed">
                  <li><strong>Account Details:</strong> Email, role (student/counselor/admin), and optional profile display name.</li>
                  <li><strong>Wellness Data:</strong> Daily mood ratings, self-reported streaks, and conversation session logs.</li>
                  <li><strong>Safety Telemetry:</strong> Anonymized severity classification scores to detect crisis triggers.</li>
                </ul>
              </section>

              <section className="space-y-3">
                <h2 className="text-xl md:text-2xl font-semibold text-[#4FD1C5] flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5" /> 3. Dual-Layer Crisis Detection & Safety Exceptions
                </h2>
                <p className="text-[#F8FAFC]/80 leading-relaxed">
                  Your conversations remain strictly private. However, in the rare event our real-time crisis detection engine flags imminent risk of self-harm or bodily harm, the platform provides direct links and phone routing to crisis helplines (such as Tele-MANAS 14416 or local emergency services 112) to ensure user safety.
                </p>
              </section>

              <section id="cookies" className="space-y-3">
                <h2 className="text-xl md:text-2xl font-semibold text-[#4FD1C5]">
                  4. Cookie & Session Policy
                </h2>
                <p className="text-[#F8FAFC]/80 leading-relaxed">
                  We use secure, HttpOnly cookies solely for authentication and session renewal. We do not use third-party advertising cookies or sell user data to data brokers.
                </p>
              </section>

              <section className="space-y-3 pt-4 border-t border-[#4FD1C5]/10">
                <p className="text-sm text-[#F8FAFC]/60">
                  Have questions about privacy? Reach out anytime at{' '}
                  <Link to="/contact" className="text-[#4FD1C5] underline hover:opacity-80">
                    support@impactai.com or our Contact page
                  </Link>.
                </p>
              </section>
            </div>
          </ScrollFadeIn>
        </main>

        <Footer />
      </div>
    </PageTransition>
  );
}
