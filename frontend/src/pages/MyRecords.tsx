import { useEffect, useState } from "react";
import { api } from "../api/client";

interface TraineeProfile {
  id: string;
  full_name: string;
  enrollment_number: string;
  batch_id: string;
  date_of_birth: string;
  gender: string;
  personnel_category: string;
}

interface PhysicalResult {
  id: string;
  raw_value: number;
  computed_grade: "excellent" | "good" | "satisfactory" | "fail" | null;
}

interface TrainingRecordOut {
  id: string;
  subject_name: string;
  instructor_name: string;
  indoor_outdoor: string;
  periods_attended: number;
  periods_total: number;
}

interface WeeklyTestOut {
  id: string;
  subject: string;
  percentage: number;
  result_status: string;
}

interface FinalExaminationOut {
  aggregate_marks: number;
  final_percentage: number;
  merit_position: number | null;
}

const GRADE_STYLES: Record<string, string> = {
  excellent: "bg-indiagreen text-white",
  good: "bg-navy text-white",
  satisfactory: "bg-gold text-white",
  fail: "bg-signal text-white",
};

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white border border-line mb-6">
      <div className="px-5 py-3 text-xs uppercase tracking-wide text-ink-soft border-b border-line font-medium">
        {title}
      </div>
      {children}
    </div>
  );
}

export default function MyRecords() {
  const [profile, setProfile] = useState<TraineeProfile | null>(null);
  const [physicalResults, setPhysicalResults] = useState<PhysicalResult[]>([]);
  const [trainingRecords, setTrainingRecords] = useState<TrainingRecordOut[]>([]);
  const [weeklyTests, setWeeklyTests] = useState<WeeklyTestOut[]>([]);
  const [finalExam, setFinalExam] = useState<FinalExaminationOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    api
      .get<TraineeProfile>("/org/trainees/me")
      .then(async ({ data }) => {
        setProfile(data);
        const [physical, training, weekly, final] = await Promise.allSettled([
          api.get<PhysicalResult[]>(`/physical-evaluation/results/${data.id}`),
          api.get<TrainingRecordOut[]>(`/training-records/${data.id}`),
          api.get<WeeklyTestOut[]>(`/exams/weekly/${data.id}`),
          api.get<FinalExaminationOut>(`/exams/final/${data.id}`),
        ]);
        if (physical.status === "fulfilled") setPhysicalResults(physical.value.data);
        if (training.status === "fulfilled") setTrainingRecords(training.value.data);
        if (weekly.status === "fulfilled") setWeeklyTests(weekly.value.data);
        if (final.status === "fulfilled") setFinalExam(final.value.data);
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-sm text-ink-soft">Loading your records…</div>;

  if (error || !profile) {
    return (
      <div className="p-8 max-w-lg">
        <div className="border border-line bg-white p-6 text-sm text-ink-soft">
          No trainee profile is linked to this account yet. If this seems wrong, contact your
          training administrator.
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-2xl">
      <div className="mb-6">
        <div className="font-mono-num text-xs tracking-widest text-gold mb-1">MY RECORDS</div>
        <h1 className="font-display font-bold text-2xl text-ink">{profile.full_name}</h1>
        <p className="text-ink-soft text-sm mt-1 font-mono-num">
          {profile.enrollment_number} &middot; {profile.personnel_category}
        </p>
      </div>

      {finalExam && (
        <div className="bg-navy text-white border border-line p-5 mb-6 flex items-center justify-between">
          <div>
            <div className="text-[11px] uppercase tracking-wide text-white/60">Final Examination — Merit Position</div>
            <div className="font-mono-num text-3xl font-semibold text-gold">
              {finalExam.merit_position ?? "—"}
            </div>
          </div>
          <div className="text-right">
            <div className="text-[11px] uppercase tracking-wide text-white/60">Aggregate / Percentage</div>
            <div className="font-mono-num text-lg">
              {finalExam.aggregate_marks} &middot; {finalExam.final_percentage}%
            </div>
          </div>
        </div>
      )}

      <Section title="Physical Evaluation (BPET / PPT)">
        {physicalResults.length === 0 ? (
          <div className="px-5 py-4 text-sm text-ink-soft">No results recorded yet.</div>
        ) : (
          physicalResults.map((r) => (
            <div key={r.id} className="register-row px-5 py-3 flex items-center justify-between">
              <span className="font-mono-num text-sm">{r.raw_value}</span>
              <span className={`px-2.5 py-0.5 text-xs font-medium uppercase tracking-wide ${GRADE_STYLES[r.computed_grade ?? "fail"]}`}>
                {r.computed_grade ?? "N/A"}
              </span>
            </div>
          ))
        )}
      </Section>

      <Section title="Training Records">
        {trainingRecords.length === 0 ? (
          <div className="px-5 py-4 text-sm text-ink-soft">No training records yet.</div>
        ) : (
          trainingRecords.map((r) => (
            <div key={r.id} className="register-row px-5 py-3">
              <div className="flex justify-between items-baseline">
                <span className="text-sm font-medium">{r.subject_name}</span>
                <span className="font-mono-num text-xs text-ink-soft uppercase">{r.indoor_outdoor}</span>
              </div>
              <div className="text-xs text-ink-soft">
                {r.instructor_name} &middot; {r.periods_attended}/{r.periods_total} periods
              </div>
            </div>
          ))
        )}
      </Section>

      <Section title="Weekly Tests">
        {weeklyTests.length === 0 ? (
          <div className="px-5 py-4 text-sm text-ink-soft">No weekly tests recorded yet.</div>
        ) : (
          weeklyTests.map((r) => (
            <div key={r.id} className="register-row px-5 py-3 flex items-center justify-between">
              <span className="text-sm">{r.subject}</span>
              <div className="flex items-center gap-3">
                <span className="font-mono-num text-sm">{r.percentage}%</span>
                <span className={`px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide ${r.result_status === "pass" ? "bg-indiagreen text-white" : "bg-signal text-white"}`}>
                  {r.result_status}
                </span>
              </div>
            </div>
          ))
        )}
      </Section>
    </div>
  );
}
