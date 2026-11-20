import { Link } from 'react-router-dom';
import { useEffect, useState } from 'react';
import {
  ArrowRight,
  Brain,
  Calendar,
  Phone,
  Smile,
  Wind,
  BookOpen,
  Heart,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import QuickMoodCheckIn from '@/components/dashboard/QuickMoodCheckIn';
import FloatingMoodButton from '@/components/dashboard/FloatingMoodButton';
import { useActivityLog, useMoodTracking } from '@/hooks/useDashboardFeatures';

interface Institution {
  name: string;
  location?: string;
  type?: string;
  id?: string;
}

const moodLabels: Record<number, string> = {
  1: 'Very low',
  2: 'Low',
  3: 'Steady',
  4: 'Good',
  5: 'Great',
};

const StudentDashboard = () => {
  const { user } = useAuth();
  const [selectedInstitution, setSelectedInstitution] = useState<Institution | null>(null);
  const { logActivity } = useActivityLog();
  const { moods, getTodayMood, getWeeklyMoodAverage } = useMoodTracking();

  useEffect(() => {
    const institution = localStorage.getItem('selected_institution');
    if (institution) {
      try {
        setSelectedInstitution(JSON.parse(institution));
      } catch {
        setSelectedInstitution(null);
      }
    }
    logActivity('resource', 'Visited Student Dashboard', 'Dashboard access');
  }, [logActivity]);

  const firstName = user?.name?.split(' ')[0] ?? 'there';
  const todayMood = getTodayMood();
  const weeklyAverage = getWeeklyMoodAverage();
  const recentMoods = moods.slice(-7);
  const hour = new Date().getHours();
  const greeting =
    hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';

  return (
    <main className="min-h-[calc(100vh-4rem)] bg-[#F7F6F0]">
      <div className="mx-auto w-full max-w-[1280px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        <section className="grid gap-5 lg:grid-cols-[1.45fr_.55fr]">
          <div className="dot-pattern border-2 border-black bg-[#FFE17C] p-6 shadow-[8px_8px_0_#000] sm:p-8">
            <p className="text-xs font-black uppercase tracking-[.16em]">{greeting}</p>
            <h1 className="mt-3 max-w-xl text-[clamp(2.5rem,6vw,4.8rem)] leading-[.92]">
              {firstName}, how is today feeling?
            </h1>
            <p className="mt-5 max-w-xl text-base leading-relaxed">
              Take a breath, check in with yourself, or begin a conversation with Zenith.
            </p>
            {selectedInstitution && (
              <div className="mt-5 inline-flex border-2 border-black bg-white px-3 py-2 text-sm font-bold">
                {selectedInstitution.name}
              </div>
            )}
          </div>

          <div className="flex flex-col justify-between border-2 border-black bg-[#171E19] p-6 text-white shadow-[8px_8px_0_#000]">
            <div>
              <div className="flex h-12 w-12 items-center justify-center border-2 border-white bg-[#FFE17C] text-[#171E19]">
                <Brain className="h-6 w-6" />
              </div>
              <p className="mt-6 text-xs font-black uppercase tracking-[.16em] text-[#FFE17C]">
                Zenith
              </p>
              <h2 className="mt-2 text-3xl !text-white">Have room to talk.</h2>
            </div>
            <Link
              to="/app/chat"
              className="brutal-button mt-8 inline-flex items-center justify-center gap-2 px-5 py-3"
            >
              Open Zenith <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </section>

        <section
          id="check-in"
          className="mt-8 grid scroll-mt-24 gap-5 lg:grid-cols-[1fr_.65fr]"
        >
          <div className="border-2 border-black bg-white p-5 shadow-[4px_4px_0_#000] sm:p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-black uppercase tracking-[.14em]">Mood check-in</p>
                <h2 className="mt-2 text-3xl">What is here today?</h2>
              </div>
              {todayMood && (
                <span className="border-2 border-black bg-[#B7C6C2] px-3 py-2 text-sm font-black">
                  {moodLabels[todayMood.mood]}
                </span>
              )}
            </div>
            <div className="mt-6">
              <QuickMoodCheckIn
                variant="default"
                showStreak={false}
                showTitle={false}
              />
            </div>
          </div>

          <div className="border-2 border-black bg-[#B7C6C2] p-5 shadow-[4px_4px_0_#000] sm:p-6">
            <p className="text-xs font-black uppercase tracking-[.14em]">Recent mood</p>
            {recentMoods.length > 0 ? (
              <>
                <div className="mt-5 flex items-end justify-between gap-2">
                  {recentMoods.map((entry, index) => (
                    <div
                      key={`${entry.timestamp}-${index}`}
                      className="flex min-w-0 flex-1 flex-col items-center gap-2"
                    >
                      <div
                        className="w-full border-2 border-black bg-white"
                        style={{ height: `${24 + entry.mood * 11}px` }}
                        title={`${moodLabels[entry.mood]} — ${new Date(entry.timestamp).toLocaleDateString()}`}
                      />
                      <span className="text-[10px] font-bold">
                        {new Date(entry.timestamp).toLocaleDateString(undefined, {
                          weekday: 'narrow',
                        })}
                      </span>
                    </div>
                  ))}
                </div>
                <p className="mt-5 text-sm font-bold">
                  Weekly average: {weeklyAverage ? `${weeklyAverage}/5` : 'No entries'}
                </p>
              </>
            ) : (
              <div className="mt-5 border-t-2 border-black pt-5">
                <h3 className="text-xl">No mood entries yet</h3>
                <p className="mt-2 text-sm leading-relaxed">
                  Your check-in history will appear here after you log how you feel.
                </p>
              </div>
            )}
          </div>
        </section>

        <section className="mt-8 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          <Link to="/app/breathing" className="brutal-card min-h-[190px] p-6">
            <Wind className="h-7 w-7" />
            <h2 className="mt-10 text-2xl">Take a breathing pause</h2>
            <p className="mt-2 text-sm leading-relaxed">
              Choose a guided 4-7-8, box, coherent or bellows exercise.
            </p>
          </Link>
          <Link to="/app/resources" className="brutal-card min-h-[190px] bg-[#B7C6C2] p-6">
            <BookOpen className="h-7 w-7" />
            <h2 className="mt-10 text-2xl">Explore resources</h2>
            <p className="mt-2 text-sm leading-relaxed">
              Read practical wellness guides and support articles.
            </p>
          </Link>
          <Link to="/app/booking" className="brutal-card min-h-[190px] bg-[#171E19] p-6 text-white">
            <Calendar className="h-7 w-7 text-[#FFE17C]" />
            <h2 className="mt-10 text-2xl !text-white">Find a session</h2>
            <p className="mt-2 text-sm leading-relaxed text-[#B7C6C2]">
              Continue to the counselling appointment flow.
            </p>
          </Link>
        </section>

        <section className="mt-8 border-2 border-black bg-white p-5 shadow-[4px_4px_0_#000] sm:p-6">
          <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-center">
            <div>
              <p className="text-xs font-black uppercase tracking-[.14em]">Immediate support</p>
              <h2 className="mt-2 text-2xl">If you need help right now</h2>
              <p className="mt-2 max-w-2xl text-sm leading-relaxed text-[#171E19]/70">
                Contact local emergency services or an established crisis line. ImpactAI does not replace professional care.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <a href="tel:14416" className="brutal-button inline-flex items-center gap-2 px-4 py-3">
                <Phone className="h-4 w-4" /> Tele-MANAS 14416
              </a>
              <a href="tel:+912227546669" className="brutal-outline inline-flex items-center px-4 py-3 text-sm font-bold">
                AASRA
              </a>
            </div>
          </div>
        </section>
      </div>
      <FloatingMoodButton position="bottom-right" showOnlyIfNotLogged={false} />
    </main>
  );
};

export default StudentDashboard;
