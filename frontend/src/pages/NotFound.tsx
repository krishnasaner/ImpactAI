import { Link } from 'react-router-dom';
import { Home, MessageCircle, HelpCircle } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#FFE17C] dot-pattern text-[#171E19]">
      <header className="p-5">
        <Link
          to="/"
          className="inline-block border-2 border-black bg-white p-2 shadow-[4px_4px_0_#000]"
        >
          <img
            src="/ImpactAI_logo.png"
            alt="ImpactAI"
            className="h-10 w-auto"
          />
        </Link>
      </header>
      <main className="impact-shell flex min-h-[calc(100vh-80px)] items-center py-10">
        <div className="brutal-card-lg max-w-3xl p-7 sm:p-12">
          <p className="text-sm font-black uppercase tracking-[.18em]">
            404 / wrong turn
          </p>
          <h1 className="mt-3 text-[clamp(5rem,18vw,10rem)] leading-[.78]">
            404
          </h1>
          <h2 className="mt-8 text-4xl">This page is not here.</h2>
          <p className="mt-3 max-w-xl text-lg text-[#171E19]/70">
            The link may have moved. You can return to ImpactAI or go straight to
            support.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link
              to="/"
              className="brutal-button inline-flex items-center justify-center px-6 py-3"
            >
              <Home className="h-4 w-4" />
              Back home
            </Link>
            <Link
              to="/app/chat"
              className="brutal-outline inline-flex items-center justify-center px-6 py-3"
            >
              <MessageCircle className="h-4 w-4" />
              Talk with Zenith
            </Link>
            <Link
              to="/contact"
              className="brutal-outline inline-flex items-center justify-center px-6 py-3"
            >
              <HelpCircle className="h-4 w-4" />
              Contact support
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
