import React from 'react';
import { Link } from 'react-router-dom';
import Header from '@/components/layout/Header';
import Footer from '@/components/layout/Footer';
import PageTransition from '@/components/ui/PageTransition';
import ScrollFadeIn from '@/components/ui/ScrollFadeIn';
import { FileText, AlertTriangle, ShieldCheck, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function TermsOfService() {
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
                <FileText className="h-3.5 w-3.5" />
                Service Agreement
              </div>
              <h1 className="text-3xl md:text-5xl font-bold mb-4 tracking-tight">Terms of Service</h1>
              <p className="text-[#F8FAFC]/70 text-base md:text-lg">
                Last updated: July 2026. Please read these terms carefully before using ImpactAI.
              </p>
            </div>

            <div className="space-y-8 bg-[#0E3440]/30 border border-[#4FD1C5]/10 rounded-2xl p-6 md:p-10 backdrop-blur-sm">
              <section className="space-y-3">
                <h2 className="text-xl md:text-2xl font-semibold text-[#4FD1C5] flex items-center gap-2">
                  <ShieldCheck className="h-5 w-5" /> 1. Scope of the Platform
                </h2>
                <p className="text-[#F8FAFC]/80 leading-relaxed">
                  ImpactAI is a digital wellness platform providing conversational AI companionship, peer community forums, and professional counseling booking. ImpactAI is intended to supplement, not replace, clinical psychiatric care or emergency hospital services.
                </p>
              </section>

              <section className="space-y-3">
                <h2 className="text-xl md:text-2xl font-semibold text-[#4FD1C5] flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-amber-400" /> 2. Emergency & Crisis Situations
                </h2>
                <p className="text-[#F8FAFC]/80 leading-relaxed">
                  If you are experiencing a medical emergency, acute psychiatric crisis, or thinking about harming yourself or others, immediately contact emergency services (112 in India, 911 in the US) or call national helplines such as Tele-MANAS (14416) or AASRA.
                </p>
              </section>

              <section className="space-y-3">
                <h2 className="text-xl md:text-2xl font-semibold text-[#4FD1C5]">
                  3. Community & Respectful Use
                </h2>
                <p className="text-[#F8FAFC]/80 leading-relaxed">
                  Users agree to treat peers and counselors with respect. Harassment, hateful speech, and promotion of self-harm are strictly forbidden and will result in immediate suspension.
                </p>
              </section>

              <section className="space-y-3 pt-4 border-t border-[#4FD1C5]/10">
                <p className="text-sm text-[#F8FAFC]/60">
                  Questions regarding these terms? Contact us at{' '}
                  <Link to="/contact" className="text-[#4FD1C5] underline hover:opacity-80">
                    our Contact page
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
