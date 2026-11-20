import { useEffect, useState } from 'react';
import { Pause, Play, RotateCcw, Wind } from 'lucide-react';
import { Button } from '@/components/ui/button';

type ExerciseId = '478' | 'box' | 'coherent' | 'bellows';
type Phase = 'inhale' | 'hold' | 'exhale' | 'holdEmpty';

interface Exercise {
  id: ExerciseId;
  name: string;
  description: string;
  pattern: { inhale: number; hold: number; exhale: number; holdEmpty?: number };
  minutes: number;
}

const exercises: Exercise[] = [
  { id: '478', name: '4-7-8 Breathing', description: 'A steady pattern for settling down.', pattern: { inhale: 4, hold: 7, exhale: 8 }, minutes: 3 },
  { id: 'box', name: 'Box Breathing', description: 'Even counts for focus and composure.', pattern: { inhale: 4, hold: 4, exhale: 4, holdEmpty: 4 }, minutes: 5 },
  { id: 'coherent', name: 'Coherent Breathing', description: 'A simple, balanced five-count rhythm.', pattern: { inhale: 5, hold: 0, exhale: 5 }, minutes: 10 },
  { id: 'bellows', name: 'Bellows Breath', description: 'An energising two-count rhythm.', pattern: { inhale: 2, hold: 0, exhale: 2 }, minutes: 2 },
];

const BreathingExercises = () => {
  const [exercise, setExercise] = useState(exercises[0]);
  const [active, setActive] = useState(false);
  const [phase, setPhase] = useState<Phase>('inhale');
  const [phaseElapsed, setPhaseElapsed] = useState(0);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const totalSeconds = exercise.minutes * 60;

  useEffect(() => {
    if (!active) return;
    const timer = window.setInterval(() => {
      setElapsedSeconds((current) => {
        if (current + 1 >= totalSeconds) {
          setActive(false);
          setPhaseElapsed(0);
          return totalSeconds;
        }
        return current + 1;
      });
      setPhaseElapsed((current) => {
        const duration = exercise.pattern[phase];
        if (duration <= 0) return 0;
        if (current + 1 >= duration) {
          const phases: Phase[] = exercise.pattern.holdEmpty
            ? ['inhale', 'hold', 'exhale', 'holdEmpty']
            : exercise.pattern.hold > 0
              ? ['inhale', 'hold', 'exhale']
              : ['inhale', 'exhale'];
          setPhase(phases[(phases.indexOf(phase) + 1) % phases.length]);
          return 0;
        }
        return current + 1;
      });
    }, 1000);
    return () => window.clearInterval(timer);
  }, [active, exercise, phase, totalSeconds]);

  const reset = () => {
    setActive(false);
    setPhase('inhale');
    setPhaseElapsed(0);
    setElapsedSeconds(0);
  };

  const selectExercise = (id: ExerciseId) => {
    setExercise(exercises.find((item) => item.id === id) ?? exercises[0]);
    reset();
  };

  const phaseLabel =
    phase === 'inhale'
      ? 'Breathe in'
      : phase === 'exhale'
        ? 'Breathe out'
        : phase === 'holdEmpty'
          ? 'Rest empty'
          : 'Hold';
  const phaseDuration = exercise.pattern[phase];
  const remaining = phaseDuration ? Math.max(0, phaseDuration - phaseElapsed) : 0;
  const progress = totalSeconds ? (elapsedSeconds / totalSeconds) * 100 : 0;
  const scale =
    phase === 'inhale'
      ? 0.75 + (phaseElapsed / Math.max(1, phaseDuration)) * 0.25
      : phase === 'exhale'
        ? 1 - (phaseElapsed / Math.max(1, phaseDuration)) * 0.25
        : 1;

  return (
    <main className="min-h-[calc(100vh-4rem)] bg-[#F7F6F0]">
      <div className="mx-auto max-w-[1280px] px-4 py-6 sm:px-6 lg:px-8">
        <header className="flex flex-col justify-between gap-4 border-b-2 border-black pb-5 sm:flex-row sm:items-end">
          <div>
            <p className="text-xs font-black uppercase tracking-[.16em]">Mindful pause</p>
            <h1 className="mt-2 text-[clamp(2.5rem,6vw,4.5rem)] leading-none">BREATH WITH CARE.</h1>
          </div>
          <div className="flex items-center gap-2 border-2 border-black bg-white px-3 py-2 text-sm font-bold shadow-[4px_4px_0_#000]">
            <Wind className="h-4 w-4" />
            {exercise.minutes} minute session
          </div>
        </header>

        <div className="mt-6 grid gap-5 lg:grid-cols-[280px_1fr]">
          <aside className="border-2 border-black bg-white p-4 shadow-[4px_4px_0_#000]">
            <p className="text-xs font-black uppercase tracking-[.14em]">Choose a rhythm</p>
            <div className="mt-4 space-y-2">
              {exercises.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => selectExercise(item.id)}
                  className={`w-full border-2 px-4 py-3 text-left transition-colors ${
                    exercise.id === item.id
                      ? 'border-black bg-[#FFE17C] shadow-[3px_3px_0_#000]'
                      : 'border-transparent hover:border-black hover:bg-[#F7F6F0]'
                  }`}
                >
                  <span className="block font-black">{item.name}</span>
                  <span className="mt-1 block text-xs leading-relaxed text-[#171E19]/70">{item.description}</span>
                </button>
              ))}
            </div>
          </aside>

          <section className="dot-pattern flex min-h-[520px] flex-col items-center justify-center border-2 border-black bg-[#171E19] p-5 text-white shadow-[8px_8px_0_#000] sm:p-8">
            <div
              className="flex h-72 w-72 max-w-[70vw] items-center justify-center rounded-full border-[3px] border-black bg-[#B7C6C2] text-[#171E19] shadow-[8px_8px_0_#FFE17C] transition-transform duration-1000"
              style={{ transform: `scale(${scale})` }}
            >
              <div className="text-center">
                <p className="text-xs font-black uppercase tracking-[.18em]">{active ? 'Current phase' : 'Ready'}</p>
                <h2 className="mt-3 text-4xl !text-[#171E19]">{active ? phaseLabel : 'Begin'}</h2>
                {active && <p className="mt-2 text-2xl font-black">{remaining}</p>}
              </div>
            </div>

            <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
              {!active ? (
                <Button type="button" onClick={() => setActive(true)} className="brutal-button h-12 px-7">
                  <Play className="h-5 w-5" /> Start
                </Button>
              ) : (
                <Button type="button" variant="outline" onClick={() => setActive(false)} className="h-12 border-white bg-white px-7 text-[#171E19]">
                  <Pause className="h-5 w-5" /> Pause
                </Button>
              )}
              <Button type="button" variant="outline" onClick={reset} className="h-12 border-white bg-transparent px-7 text-white">
                <RotateCcw className="h-5 w-5" /> Reset
              </Button>
            </div>

            <div className="mt-8 w-full max-w-xl">
              <div className="mb-2 flex justify-between text-xs font-bold">
                <span>Session progress</span>
                <span>{elapsedSeconds}s / {totalSeconds}s</span>
              </div>
              <div className="h-3 border-2 border-white bg-[#171E19]">
                <div className="h-full bg-[#FFE17C] transition-[width] duration-500" style={{ width: `${progress}%` }} />
              </div>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
};

export default BreathingExercises;
