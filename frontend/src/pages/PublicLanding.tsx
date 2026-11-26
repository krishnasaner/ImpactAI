import { Link } from 'react-router-dom';
import { ArrowRight, BookOpen, Brain, CalendarCheck, Heart, MessageCircle, MoonStar, ShieldCheck, Users } from 'lucide-react';

const nav = [
  ['About', '/about'], ['Features', '#features'], ['Resources', '/app/resources'], ['Contact', '/contact'],
];

export default function PublicLanding() {
  return (
    <div className="min-h-screen overflow-x-hidden bg-white text-[#171E19]">
      <header className="sticky top-0 z-50 border-b-2 border-black bg-white">
        <div className="impact-shell flex h-20 items-center justify-between">
          <Link to="/" aria-label="ImpactAI home" className="flex items-center gap-3">
            <img src="/ImpactAI_logo.png" alt="ImpactAI" className="h-11 md:h-12 w-auto max-w-[170px] object-contain" />
          </Link>
          <nav className="hidden items-center gap-7 md:flex" aria-label="Primary navigation">
            {nav.map(([label, href]) => href.startsWith('/') ? <Link key={label} to={href} className="font-bold hover:underline">{label}</Link> : <a key={label} href={href} className="font-bold hover:underline">{href === '#features' ? 'Features' : label}</a>)}
          </nav>
          <div className="flex items-center gap-2">
            <Link to="/login" className="hidden px-3 py-2 font-bold sm:inline">Log in</Link>
            <Link to="/signup" className="brutal-button hidden px-5 py-2 sm:inline-flex">Get started</Link>
          </div>
        </div>
      </header>

      <main>
        <section className="border-b-2 border-black bg-[#FFE17C]">
          <div className="impact-shell grid min-h-[650px] items-center gap-10 py-16 lg:grid-cols-[1.08fr_.92fr]">
            <div className="relative z-10">
              <div className="mb-6 inline-flex items-center gap-2 border-2 border-black bg-white px-3 py-2 text-sm font-bold shadow-[4px_4px_0_#000]">
                <Heart className="h-4 w-4 fill-[#B7C6C2]" /> Built around student well-being
              </div>
              <h1 className="max-w-[780px] text-[clamp(3.2rem,8vw,7.2rem)] font-black leading-[0.88]">
                YOUR WELL-BEING<br /><span className="inline-block rotate-[-2deg] bg-white px-3 pb-2">DESERVES</span><br />ATTENTION.
              </h1>
              <p className="mt-8 max-w-xl text-lg font-medium leading-relaxed md:text-xl">
                ImpactAI brings Zenith conversations, mood awareness, breathing tools and pathways to support into one approachable place.
              </p>
              <div className="mt-8 flex flex-col gap-4 sm:flex-row">
                <Link to="/signup" className="brutal-button inline-flex items-center justify-center px-7 py-4">Explore ImpactAI <ArrowRight className="h-5 w-5" /></Link>
                <Link to="/app/chat" className="brutal-outline inline-flex items-center justify-center px-7 py-4 font-bold">Meet Zenith</Link>
              </div>
            </div>

            <div className="relative mx-auto w-full max-w-[520px]">
              <div className="absolute -right-4 -top-5 z-20 border-2 border-black bg-[#B7C6C2] px-4 py-3 text-sm font-black rotate-3 shadow-[4px_4px_0_#000]">ZENITH IS HERE</div>
              <div className="brutal-card-lg overflow-hidden">
                <div className="flex items-center justify-between border-b-2 border-black bg-[#171E19] px-5 py-4 text-white">
                  <div className="flex items-center gap-3"><div className="h-10 w-10 rounded-full border-2 border-white bg-[#FFE17C]" /><div><b>Zenith</b><div className="text-xs text-[#B7C6C2]">Wellness companion</div></div></div>
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <div className="min-h-[430px] bg-[#F7F7F2] p-5">
                  <div className="ml-auto max-w-[82%] border-2 border-black bg-[#FFE17C] p-4 shadow-[4px_4px_0_#000]"><b>You</b><p className="mt-1 text-sm">I have a presentation and my head feels overloaded.</p></div>
                  <div className="mt-6 max-w-[88%] border-2 border-black bg-white p-4 shadow-[4px_4px_0_#000]"><b>Zenith</b><p className="mt-2 text-sm leading-relaxed">That sounds really demanding. Let&apos;s slow down for a moment. Would you like to try a 60-second breathing reset or talk through what feels most difficult?</p></div>
                  <div className="mt-5 flex gap-2"><button className="border-2 border-black bg-[#B7C6C2] px-3 py-2 text-sm font-bold">Try breathing</button><button className="border-2 border-black bg-white px-3 py-2 text-sm font-bold">Talk it through</button></div>
                  <div className="mt-8 border-t-2 border-black pt-4 text-sm font-bold text-[#171E19]/60">Message Zenith…</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="features" className="border-b-2 border-black py-20">
          <div className="impact-shell">
            <div className="grid gap-8 md:grid-cols-[.7fr_1.3fr]">
              <div><span className="font-black text-sm uppercase tracking-[.18em]">01 / Support</span><h2 className="mt-4 text-5xl font-black leading-[.95] md:text-7xl">TOOLS THAT MEET YOU WHERE YOU ARE.</h2></div>
              <p className="max-w-xl self-end text-lg leading-relaxed font-medium">Student life is full. ImpactAI is designed to make a first step feel simple, not clinical or overwhelming.</p>
            </div>
            <div className="mt-12 grid gap-5 md:grid-cols-12">
              <Feature icon={<Brain />} title="Zenith" copy="A supportive AI companion for reflection and next-step ideas. Not a diagnosis or replacement for care." className="bg-[#FFE17C] md:col-span-7" />
              <Feature icon={<MoonStar />} title="Mood check-ins" copy="Notice patterns in a clear, private-in-practice check-in history." className="bg-[#B7C6C2] md:col-span-5" />
              <Feature icon={<BookOpen />} title="Resources" copy="Explore breathing guides and readable wellness articles." className="bg-white md:col-span-4" />
              <Feature icon={<CalendarCheck />} title="Counselling" copy="Find available counselling sessions and keep track of bookings." className="bg-[#171E19] text-white md:col-span-4 dark-feature" />
              <Feature icon={<Users />} title="Community" copy="Read and share in moderated student discussions." className="bg-[#FFE17C] md:col-span-4" />
            </div>
          </div>
        </section>

        <section className="border-b-2 border-black bg-[#171E19] py-20 text-white">
          <div className="impact-shell">
            <span className="font-black text-sm uppercase tracking-[.18em] text-[#FFE17C]">02 / How it works</span>
            <h2 className="mt-4 max-w-3xl text-5xl font-black leading-none md:text-7xl">START SMALL. KEEP CHOICE WITH YOU.</h2>
            <div className="mt-12 grid gap-5 md:grid-cols-3">
              {[['01','Check in','Name what you are feeling without pressure or judgment.'],['02','Explore','Talk with Zenith or use a breathing and wellness tool.'],['03','Choose next','Track a check-in or explore professional and community support.']].map(([n,t,c]) => <div key={n} className="border-2 border-white bg-[#171E19] p-6"><b className="text-[#FFE17C]">{n}</b><h3 className="mt-12 text-3xl !text-white">{t}</h3><p className="mt-3 text-[#B7C6C2]">{c}</p></div>)}
            </div>
          </div>
        </section>

        <section className="py-20">
          <div className="impact-shell grid gap-8 md:grid-cols-[1fr_.65fr]">
            <div className="brutal-card-lg p-8 md:p-12"><ShieldCheck className="h-10 w-10" /><h2 className="mt-8 text-4xl font-black md:text-6xl">PRIVACY & RESPONSIBLE USE.</h2><p className="mt-5 max-w-2xl text-lg leading-relaxed">Zenith provides general wellbeing support, not medical diagnosis or treatment. Information you share may be processed to provide chat and platform features. Review the privacy notice and avoid sharing identifying details when that is a concern.</p></div>
            <div className="border-2 border-black bg-[#FFE17C] p-8 shadow-[8px_8px_0_#000]"><h3 className="text-3xl">Need immediate help?</h3><p className="mt-3 leading-relaxed">If you may be in immediate danger, contact local emergency services. For crisis support in India, Tele-MANAS is available at <b>14416</b>.</p><a href="tel:14416" className="brutal-outline mt-6 inline-flex px-5 py-3 font-bold">Call 14416</a></div>
          </div>
        </section>

        <section className="border-t-2 border-black bg-[#B7C6C2]">
          <div className="impact-shell flex flex-col items-start justify-between gap-8 py-14 md:flex-row md:items-center"><div><h2 className="text-4xl font-black md:text-6xl">TAKE ONE STEP.</h2><p className="mt-2 font-medium">No pressure. Just a place to begin.</p></div><Link to="/signup" className="brutal-button inline-flex items-center px-8 py-4">Create an account <ArrowRight className="h-5 w-5" /></Link></div>
        </section>
      </main>

      <Footer />
    </div>
  );
}

function Feature({ icon, title, copy, className }: { icon: React.ReactNode; title: string; copy: string; className: string }) {
  return <article className={`brutal-card min-h-[250px] p-6 ${className}`}>{icon}<h3 className={`mt-16 text-3xl ${className.includes('text-white') ? '!text-white' : ''}`}>{title}</h3><p className={`mt-3 font-medium leading-relaxed ${className.includes('text-white') ? 'text-[#B7C6C2]' : ''}`}>{copy}</p></article>;
}

function Footer() {
  return <footer className="border-t-2 border-black bg-white"><div className="impact-shell flex flex-col gap-6 py-10 md:flex-row md:items-end md:justify-between"><div><img src="/ImpactAI_logo.png" alt="ImpactAI" className="h-12 w-auto max-w-[175px] object-contain"/><p className="mt-3 max-w-sm text-sm text-[#171E19]/70">Student mental well-being support through conversation, resources and connection.</p></div><nav className="grid grid-cols-2 gap-x-8 gap-y-3 text-sm font-bold"><Link to="/about">About</Link><Link to="/contact">Contact</Link><Link to="/privacy">Privacy</Link><Link to="/terms">Terms</Link></nav></div></footer>;
}
