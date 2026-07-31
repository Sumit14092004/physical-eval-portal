import { useEffect, useState, type FormEvent } from "react";
import { api } from "../api/client";
import { useBatches, BatchSelector } from "../components/BatchSelector";
import { useTrainees, TraineeSelect, type TraineeOption } from "../components/TraineeSelect";

type Tab = "weekly" | "monthly" | "quarterly" | "final";

const TABS: { id: Tab; label: string }[] = [
  { id: "weekly", label: "Weekly Test" },
  { id: "monthly", label: "Monthly Test" },
  { id: "quarterly", label: "Quarterly Exam" },
  { id: "final", label: "Final Examination" },
];

function Field({
  label, value, onChange, type = "text", placeholder,
}: { label: string; value: string; onChange: (v: string) => void; type?: string; placeholder?: string }) {
  return (
    <label className="block">
      <span className="text-xs font-medium text-ink-soft uppercase tracking-wide">{label}</span>
      <input
        type={type}
        step={type === "number" ? "0.01" : undefined}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="mt-1 w-full border border-line px-3 py-2 bg-paper font-mono-num text-sm focus:outline-none focus:border-navy"
      />
    </label>
  );
}

function ResultBanner({ label, value }: { label: string; value: string }) {
  return (
    <div className="mt-4 border border-line bg-paper-dim px-4 py-3 flex justify-between items-center">
      <span className="text-xs uppercase tracking-wide text-ink-soft">{label}</span>
      <span className="font-mono-num text-lg text-navy font-semibold">{value}</span>
    </div>
  );
}

// ---------- Weekly ----------
function WeeklyForm({ traineeId }: { traineeId: string }) {
  const [testDate, setTestDate] = useState(new Date().toISOString().slice(0, 10));
  const [subject, setSubject] = useState("");
  const [maxMarks, setMaxMarks] = useState("");
  const [obtained, setObtained] = useState("");
  const [result, setResult] = useState<{ percentage: number; result_status: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const { data } = await api.post("/exams/weekly", {
        trainee_id: traineeId, test_date: testDate, subject,
        maximum_marks: parseFloat(maxMarks), marks_obtained: parseFloat(obtained),
      });
      setResult(data);
    } catch {
      setError("Couldn't record this test. Check the inputs and try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <Field label="Test Date" type="date" value={testDate} onChange={setTestDate} />
        <Field label="Subject" value={subject} onChange={setSubject} placeholder="e.g. Field Craft" />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Maximum Marks" type="number" value={maxMarks} onChange={setMaxMarks} />
        <Field label="Marks Obtained" type="number" value={obtained} onChange={setObtained} />
      </div>
      {error && <div className="text-sm text-signal bg-signal-soft border border-signal/30 px-3 py-2">{error}</div>}
      <button type="submit" disabled={submitting || !traineeId} className="bg-navy text-white font-medium px-5 py-2.5 hover:bg-navy-dark transition-colors disabled:opacity-50">
        {submitting ? "Recording…" : "Record weekly test"}
      </button>
      {result && (
        <ResultBanner label={`Result: ${result.result_status.toUpperCase()}`} value={`${result.percentage}%`} />
      )}
    </form>
  );
}

// ---------- Monthly ----------
function MonthlyForm({ traineeId }: { traineeId: string }) {
  const [month, setMonth] = useState(new Date().toISOString().slice(0, 7) + "-01");
  const [subjectMarks, setSubjectMarks] = useState([{ subject: "", marks: "" }]);
  const [result, setResult] = useState<{ aggregate: number; rank: number | null } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const updateRow = (i: number, field: "subject" | "marks", value: string) =>
    setSubjectMarks((rows) => rows.map((r, idx) => (idx === i ? { ...r, [field]: value } : r)));

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const subject_wise_marks: Record<string, number> = {};
      subjectMarks.forEach((r) => {
        if (r.subject) subject_wise_marks[r.subject] = parseFloat(r.marks || "0");
      });
      const { data } = await api.post("/exams/monthly", {
        trainee_id: traineeId, month, subject_wise_marks,
      });
      setResult(data);
    } catch {
      setError("Couldn't record this test. Check the inputs and try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Field label="Month" type="date" value={month} onChange={setMonth} />
      <div>
        <span className="text-xs font-medium text-ink-soft uppercase tracking-wide">Subject-wise Marks</span>
        <div className="space-y-2 mt-1">
          {subjectMarks.map((row, i) => (
            <div key={i} className="grid grid-cols-[1fr_8rem] gap-2">
              <input
                value={row.subject}
                onChange={(e) => updateRow(i, "subject", e.target.value)}
                placeholder="Subject"
                className="border border-line px-3 py-2 bg-paper text-sm focus:outline-none focus:border-navy"
              />
              <input
                type="number"
                value={row.marks}
                onChange={(e) => updateRow(i, "marks", e.target.value)}
                placeholder="Marks"
                className="border border-line px-3 py-2 bg-paper font-mono-num text-sm focus:outline-none focus:border-navy"
              />
            </div>
          ))}
        </div>
        <button
          type="button"
          onClick={() => setSubjectMarks((r) => [...r, { subject: "", marks: "" }])}
          className="text-xs text-navy hover:text-navy-dark underline underline-offset-2 mt-2"
        >
          + Add subject
        </button>
      </div>
      {error && <div className="text-sm text-signal bg-signal-soft border border-signal/30 px-3 py-2">{error}</div>}
      <button type="submit" disabled={submitting || !traineeId} className="bg-navy text-white font-medium px-5 py-2.5 hover:bg-navy-dark transition-colors disabled:opacity-50">
        {submitting ? "Recording…" : "Record monthly test"}
      </button>
      {result && <ResultBanner label={`Aggregate — Batch Rank ${result.rank ?? "computing…"}`} value={String(result.aggregate)} />}
    </form>
  );
}

// ---------- Quarterly ----------
function QuarterlyForm({ traineeId }: { traineeId: string }) {
  const [quarter, setQuarter] = useState("Q1");
  const [written, setWritten] = useState("");
  const [practical, setPractical] = useState("");
  const [pt, setPt] = useState("");
  const [firing, setFiring] = useState("");
  const [result, setResult] = useState<{ total_marks: number; percentage: number; rank: number | null } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const { data } = await api.post("/exams/quarterly", {
        trainee_id: traineeId, quarter,
        written_marks: parseFloat(written), practical_marks: parseFloat(practical),
        pt_marks: parseFloat(pt), firing_marks: parseFloat(firing),
      });
      setResult(data);
    } catch {
      setError("Couldn't record this exam. Check the inputs and try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <label className="block">
        <span className="text-xs font-medium text-ink-soft uppercase tracking-wide">Quarter</span>
        <select value={quarter} onChange={(e) => setQuarter(e.target.value)} className="mt-1 w-full border border-line px-3 py-2 bg-paper text-sm focus:outline-none focus:border-navy">
          <option>Q1</option><option>Q2</option><option>Q3</option><option>Q4</option>
        </select>
      </label>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Written Marks" type="number" value={written} onChange={setWritten} />
        <Field label="Practical Marks" type="number" value={practical} onChange={setPractical} />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <Field label="PT Marks" type="number" value={pt} onChange={setPt} />
        <Field label="Firing Marks" type="number" value={firing} onChange={setFiring} />
      </div>
      {error && <div className="text-sm text-signal bg-signal-soft border border-signal/30 px-3 py-2">{error}</div>}
      <button type="submit" disabled={submitting || !traineeId} className="bg-navy text-white font-medium px-5 py-2.5 hover:bg-navy-dark transition-colors disabled:opacity-50">
        {submitting ? "Recording…" : "Record quarterly exam"}
      </button>
      {result && (
        <ResultBanner label={`${result.percentage}% — Batch Rank ${result.rank ?? "computing…"}`} value={String(result.total_marks)} />
      )}
    </form>
  );
}

// ---------- Final ----------
const FINAL_FIELDS: { key: string; label: string }[] = [
  { key: "written_examination", label: "Written Examination" },
  { key: "practical_examination", label: "Practical Examination" },
  { key: "pt_test", label: "PT Test" },
  { key: "bpet", label: "BPET" },
  { key: "ppt", label: "PPT" },
  { key: "firing_classification", label: "Firing Classification" },
  { key: "outdoor_assessment", label: "Outdoor Assessment" },
  { key: "indoor_assessment", label: "Indoor Assessment" },
  { key: "field_craft", label: "Field Craft" },
  { key: "battle_craft", label: "Battle Craft" },
  { key: "drill_test", label: "Drill Test" },
  { key: "weapon_test", label: "Weapon Test" },
];

function FinalForm({ traineeId }: { traineeId: string }) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [result, setResult] = useState<{ aggregate_marks: number; final_percentage: number; merit_position: number | null } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const payload: Record<string, unknown> = { trainee_id: traineeId };
      FINAL_FIELDS.forEach((f) => { payload[f.key] = parseFloat(values[f.key] || "0"); });
      const { data } = await api.post("/exams/final", payload);
      setResult(data);
    } catch {
      setError("Couldn't record the final examination. Check the inputs and try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        {FINAL_FIELDS.map((f) => (
          <Field
            key={f.key}
            label={f.label}
            type="number"
            value={values[f.key] ?? ""}
            onChange={(v) => setValues((prev) => ({ ...prev, [f.key]: v }))}
          />
        ))}
      </div>
      {error && <div className="text-sm text-signal bg-signal-soft border border-signal/30 px-3 py-2">{error}</div>}
      <button type="submit" disabled={submitting || !traineeId} className="bg-navy text-white font-medium px-5 py-2.5 hover:bg-navy-dark transition-colors disabled:opacity-50">
        {submitting ? "Recording…" : "Record final examination"}
      </button>
      {result && (
        <ResultBanner
          label={`${result.final_percentage}% — Merit Position ${result.merit_position ?? "computing…"}`}
          value={String(result.aggregate_marks)}
        />
      )}
    </form>
  );
}

export default function Examinations() {
  const { batches, selectedBatchId, setSelectedBatchId } = useBatches();
  const { trainees } = useTrainees(selectedBatchId);
  const [traineeId, setTraineeId] = useState("");
  const [tab, setTab] = useState<Tab>("weekly");

  useEffect(() => setTraineeId(""), [selectedBatchId]);

  return (
    <div className="p-8 max-w-2xl">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <div className="font-mono-num text-xs tracking-widest text-gold mb-1">MODULE 14</div>
          <h1 className="font-display font-bold text-2xl text-ink">Examinations</h1>
        </div>
        <BatchSelector batches={batches} value={selectedBatchId} onChange={setSelectedBatchId} />
      </div>

      <div className="bg-white border border-line p-6 mb-4">
        <label className="block">
          <span className="text-xs font-medium text-ink-soft uppercase tracking-wide">Trainee</span>
          <TraineeSelect trainees={trainees as TraineeOption[]} value={traineeId} onChange={setTraineeId} />
        </label>
      </div>

      <div className="flex border-b border-line mb-4">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              tab === t.id ? "border-maroon text-maroon" : "border-transparent text-ink-soft hover:text-ink"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="bg-white border border-line p-6">
        {!traineeId && <p className="text-sm text-ink-soft">Select a trainee above to begin.</p>}
        {traineeId && tab === "weekly" && <WeeklyForm traineeId={traineeId} />}
        {traineeId && tab === "monthly" && <MonthlyForm traineeId={traineeId} />}
        {traineeId && tab === "quarterly" && <QuarterlyForm traineeId={traineeId} />}
        {traineeId && tab === "final" && <FinalForm traineeId={traineeId} />}
      </div>
    </div>
  );
}
