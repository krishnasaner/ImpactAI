import { Link } from 'react-router-dom';
import { ShieldCheck } from 'lucide-react';

export default function PrivacyPolicy() {
  return <div className="min-h-screen bg-[#F7F7F2]">
    <header className="border-b-2 border-black bg-white">
      <div className="impact-shell flex h-20 items-center justify-between">
        <Link to="/">
          <img src="/ImpactAI_logo.png" alt="ImpactAI" className="h-11" />
        </Link>
        <Link to="/contact" className="font-bold underline">Contact</Link>
      </div>
    </header>
    <main className="impact-shell py-12">
      <article className="brutal-card-lg max-w-4xl p-6 md:p-10">
        <ShieldCheck className="h-10 w-10" />
        <p className="mt-6 text-sm font-black uppercase tracking-[.18em]">Legal information</p>
        <h1 className="mt-3 text-5xl font-black">Privacy notice</h1>
        <div className="mt-8 space-y-8 leading-relaxed">
          <section>
            <h2 className="text-2xl">Information used by the platform</h2>
            <p>ImpactAI may process account details, profile information, mood check-ins, chat submissions, booking details and community activity to operate the requested features.</p>
          </section>
          <section>
            <h2 className="text-2xl">AI processing</h2>
            <p>Messages sent to Zenith are transmitted to the configured backend and AI service for generating a response. Do not enter secrets or information you do not wish to process in this context.</p>
          </section>
          <section>
            <h2 className="text-2xl">Storage and access</h2>
            <p>Data is stored and managed by the platform backend and its configured services. This interface does not provide a guarantee of complete anonymity, and anonymous participation is subject to the actual backend implementation.</p>
          </section>
          <section><h2 className="text-2xl">Your choices</h2>
            <p>You can limit information shared in forms and conversations. For access, correction or deletion requests, use the contact page.</p>
          </section>
        </div>
      </article>
    </main>
  </div>;
}
