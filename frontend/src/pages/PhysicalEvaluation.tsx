import { useEffect, useState, type FormEvent } from "react";
import { api } from "../api/client";
import { useBatches, BatchSelector } from "../components/BatchSelector";
import { useTrainees, TraineeSelect } from "../components/TraineeSelect";

interface FpetActivity {
  name: string;
  max_marks: number;
}

interface FpetTemplate {
  trainee_id: string;
  gender: string;
  age: number;
  age_band: string;
  activities: FpetActivity[];
  max_total: number;
}

interface FpetResult {
  id: string;
  total_marks: number;
  max_total: number;
  percentage: number;
  grade: string;
}

interface FpetHistoryEntry extends FpetResult {
  test_date: string;
}

const AGE_BAND_LABELS: Record<string, string> = {
  below_35: "Below 35 yrs",
  "35_40": "35–40 yrs",
  "40_45": "40–45 yrs",
  female: "Female",
};

const GRADE_STYLES: Record<string, string> = {
  Excellent: "bg-indiagreen text-white",
  "Very Good": "bg-navy text-white",
  Good: "bg-gold text-white",
  Fail: "bg-signal text-white",
};

export default function PhysicalEvaluation() {
  const { batches, selectedBatchId, setSelectedBatchId } = useBatches();
  const { trainees } = useTrainees(selectedBatchId);

  const [traineeId, setTraineeId] = useState("");
  const [template, setTemplate] = useState<FpetTemplate | null>(null);
  const [templateLoading, setTemplateLoading] = useState(false);
  const [marks, setMarks] = useState<Record<string, string>>({});
  const [testDate, setTestDate] = useState(new Date().toISOString().slice(0, 10));
  const [history, setHistory] = useState<FpetHistoryEntry[]>([]);

  const [result, setResult] = useState<FpetResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => setTraineeId(""), [selectedBatchId]);

  useEffect(() => {
    if (!traineeId) {
      setTemplate(null);
      return;
    }
    setTemplateLoading(true);
    setResult(null);
    setError(null);
    api
      .get<FpetTemplate>(`/fpet/template/${traineeId}`)
      .then(({ data }) => {
        setTemplate(data);
        const blank: Record<string, string> = {};
        data.activities.forEach((a) => (blank[a.name] = ""));
        setMarks(blank);
      })
      .finally(() => setTemplateLoading(false));

    api
      .get<FpetHistoryEntry[]>(`/fpet/results/${traineeId}`)
      .then(({ data }) => setHistory(data));
  }, [traineeId]);

  const updateMark = (name: string, value: string) =>
    setMarks((m) => ({ ...m, [name]: value }));

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!template) return;
    setError(null);
    setSubmitting(true);
    try {
      const numericMarks: Record<string, number> = {};
      template.activities.forEach((a) => {
        numericMarks[a.name] = parseFloat(marks[a.name] || "0");
      });
      const { data } = await api.post<FpetHistoryEntry>("/fpet/results", {
        trainee_id: traineeId,
        test_date: testDate,
        marks: numericMarks,
      });
      setResult(data);
      setHistory((h) => [data, ...h]);
    } catch {
      setError("Couldn't record this result. Check each mark is within its maximum.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="p-8 max-w-2xl">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <div className="font-mono-num text-xs tracking-widest text-gold mb-1">FPET</div>
          <h1 className="font-display font-bold text-2xl text-ink">Physical Evaluation</h1>
        </div>
        <BatchSelector batches={batches} value={selectedBatchId} onChange={setSelectedBatchId} />
      </div>

      <div className="bg-white border border-line p-6 mb-4">
        <label className="block">
          <span className="text-xs font-medium text-ink-soft uppercase tracking-wide">Trainee</span>
          <TraineeSelect trainees={trainees} value={traineeId} onChange={setTraineeId} />
        </label>
      </div>

      {!traineeId && (
        <div className="bg-white border border-line p-6 text-sm text-ink-soft">
          Select a trainee to load their evaluation form.
        </div>
      )}

      {templateLoading && (
        <div className="bg-white border border-line p-6 text-sm text-ink-soft">Loading form…</div>
      )}

      {template && !templateLoading && (
        <form onSubmit={handleSubmit} className="bg-white border border-line p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-line pb-4">
            <div>
              <div className="text-sm font-medium">
                {template.gender} &middot; Age {template.age}
              </div>
              <div className="font-mono-num text-xs text-gold uppercase tracking-wide">
                {AGE_BAND_LABELS[template.age_band] ?? template.age_band}
              </div>
            </div>
            <label className="block">
              <span className="text-xs font-medium text-ink-soft uppercase tracking-wide">Test Date</span>
              <input
                type="date"
                required
                value={testDate}
                onChange={(e) => setTestDate(e.target.value)}
                className="mt-1 border border-line px-3 py-2 bg-paper font-mono-num text-sm focus:outline-none focus:border-navy"
              />
            </label>
          </div>

          <div className="space-y-3">
            {template.activities.map((a) => (
              <div key={a.name} className="grid grid-cols-[1fr_8rem] gap-4 items-center">
                <span className="text-sm">{a.name}</span>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    step="0.5"
                    min={0}
                    max={a.max_marks}
                    required
                    value={marks[a.name] ?? ""}
                    onChange={(e) => updateMark(a.name, e.target.value)}
                    className="w-16 border border-line px-2 py-1.5 bg-paper font-mono-num text-sm text-right focus:outline-none focus:border-navy"
                  />
                  <span className="font-mono-num text-xs text-ink-soft">/ {a.max_marks}</span>
                </div>
              </div>
            ))}
          </div>

          <div className="text-right font-mono-num text-xs text-ink-soft border-t border-line pt-3">
            Max total: {template.max_total}
          </div>

          {error && (
            <div className="text-sm text-signal bg-signal-soft border border-signal/30 px-3 py-2">{error}</div>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="bg-navy text-white font-medium px-5 py-2.5 hover:bg-navy-dark transition-colors disabled:opacity-50"
          >
            {submitting ? "Recording…" : "Record result"}
          </button>

          {result && (
            <div className="border border-line bg-paper-dim p-4 flex items-center justify-between">
              <div>
                <div className="text-xs uppercase tracking-wide text-ink-soft">Total / Percentage</div>
                <div className="font-mono-num text-lg">
                  {result.total_marks} / {result.max_total} &middot; {result.percentage}%
                </div>
              </div>
              <span className={`px-3 py-1 text-xs font-medium uppercase tracking-wide ${GRADE_STYLES[result.grade] ?? "bg-paper-dim text-ink"}`}>
                {result.grade}
              </span>
            </div>
          )}
        </form>
      )}

      {history.length > 0 && (
        <div className="mt-6 bg-white border border-line">
          <div className="px-5 py-3 text-xs uppercase tracking-wide text-ink-soft border-b border-line font-medium">
            Past FPET Results
          </div>
          {history.map((h) => (
            <div key={h.id} className="register-row px-5 py-3 flex items-center justify-between">
              <span className="font-mono-num text-xs text-ink-soft">{h.test_date}</span>
              <span className="font-mono-num text-sm">
                {h.total_marks} / {h.max_total} &middot; {h.percentage}%
              </span>
              <span className={`px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide ${GRADE_STYLES[h.grade] ?? "bg-paper-dim text-ink"}`}>
                {h.grade}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
