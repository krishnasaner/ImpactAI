import { Link } from 'react-router-dom';

export default function TermsOfService() {
  return (
    <div className="min-h-screen bg-[#F7F7F2]">
      <header className="border-b-2 border-black bg-white">
        <div className="impact-shell flex h-20 items-center justify-between">
          <Link to="/">
            <img
              src="/ImpactAI_logo.png"
              alt="ImpactAI"
              className="h-11"
            />
          </Link>
          <Link to="/contact" className="font-bold underline">
            Contact
          </Link>
        </div>
      </header>
      <main className="impact-shell py-12">
        <article className="brutal-card-lg max-w-4xl p-6 md:p-10">
          <p className="text-sm font-black uppercase tracking-[.18em]">
            Legal information
          </p>
          <h1 className="mt-3 text-5xl font-black">Terms of use</h1>
          <div className="mt-8 space-y-8 leading-relaxed">
            <section>
              <h2 className="text-2xl">Responsible use</h2>
              <p>
                ImpactAI provides supportive digital tools and pathways to
                resources. It does not diagnose, treat or prevent mental health
                conditions and does not replace professional medical care.
              </p>
            </section>
            <section>
              <h2 className="text-2xl">Community conduct</h2>
              <p>
                Users must communicate respectfully, avoid harassment and use
                reporting and moderation controls when content creates safety
                concerns.
              </p>
            </section>
            <section>
              <h2 className="text-2xl">Emergencies</h2>
              <p>
                ImpactAI is not an emergency service. If you or another person
                may be in immediate danger, contact local emergency services or a
                qualified crisis support provider.
              </p>
            </section>
            <section>
              <h2 className="text-2xl">Service availability</h2>
              <p>
                Features may change and the platform may be unavailable during
                maintenance or service outages. Counsellor availability shown in
                the application reflects information returned by the backend.
              </p>
            </section>
          </div>
        </article>
      </main>
    </div>
  );
}
