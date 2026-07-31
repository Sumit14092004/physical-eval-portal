import { useEffect, useState, type FormEvent } from "react";
import { api } from "../api/client";
import type { PhysicalResult } from "../types";
import { useBatches, BatchSelector } from "../components/BatchSelector";
import { useTrainees, TraineeSelect } from "../components/TraineeSelect";

const GRADE_STYLES: Record<string, string> = {
  excellent: "bg-indiagreen text-white",
  good: "bg-navy text-white",
  satisfactory: "bg-gold text-white",
  fail: "bg-signal text-white",
};

interface Activity {
  id: string;
  test_category: string;
  name: string;
  unit: string;
}

export default function PhysicalEvaluation() {
  const { batches, selectedBatchId, setSelectedBatchId } = useBatches();
  const { trainees } = useTrainees(selectedBatchId);
  const [activities, setActivities] = useState<Activity[]>([]);

  const [traineeId, setTraineeId] = useState("");
  const [activityId, setActivityId] = useState("");
  const [testDate, setTestDate] = useState(
    new Date().toISOString().slice(0, 10)
  );
  const [rawValue, setRawValue] = useState("");
  const [result, setResult] = useState<PhysicalResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api.get<Activity[]>("/physical-evaluation/activities").then((res) => setActivities(res.data));
  }, []);

  useEffect(() => {
    setTraineeId("");
  }, [selectedBatchId]);

  const selectedActivity = activities.find((a) => a.id === activityId);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    setSubmitting(true);
    try {
      const { data } = await api.post<PhysicalResult>(
        "/physical-evaluation/results",
        {
          trainee_id: traineeId,
          activity_id: activityId,
          test_date: testDate,
          raw_value: parseFloat(rawValue),
        }
      );
      setResult(data);
    } catch {
      setError("Couldn't record this result. Please check the inputs and try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="p-8 max-w-lg">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <div className="font-mono-num text-xs tracking-widest text-gold mb-1">
            BPET / PPT
          </div>
          <h1 className="font-display text-3xl font-semibold text-ink">
            Record Physical Test Result
          </h1>
        </div>
        <BatchSelector batches={batches} value={selectedBatchId} onChange={setSelectedBatchId} />
      </div>
      <p className="text-ink-soft text-sm mb-6">
        Grade is calculated automatically against the trainee's age-band
        standard — Excellent / Good / Satisfactory / Fail.
      </p>

      <form onSubmit={handleSubmit} className="bg-white border border-line p-6 space-y-4">
        <label className="block">
          <span className="text-xs font-medium text-ink-soft uppercase tracking-wide">
            Trainee
          </span>
          <TraineeSelect trainees={trainees} value={traineeId} onChange={setTraineeId} />
        </label>

        <label className="block">
          <span className="text-xs font-medium text-ink-soft uppercase tracking-wide">
            Activity
          </span>
          <select
            required
            value={activityId}
            onChange={(e) => setActivityId(e.target.value)}
            className="mt-1 w-full border border-line px-3 py-2 bg-paper text-sm focus:outline-none focus:border-navy"
          >
            <option value="" disabled>
              Select an activity…
            </option>
            <optgroup label="BPET">
              {activities.filter((a) => a.test_category === "bpet").map((a) => (
                <option key={a.id} value={a.id}>{a.name}</option>
              ))}
            </optgroup>
            <optgroup label="PPT">
              {activities.filter((a) => a.test_category === "ppt").map((a) => (
                <option key={a.id} value={a.id}>{a.name}</option>
              ))}
            </optgroup>
          </select>
        </label>

        <div className="grid grid-cols-2 gap-4">
          <label className="block">
            <span className="text-xs font-medium text-ink-soft uppercase tracking-wide">
              Test Date
            </span>
            <input
              type="date"
              required
              value={testDate}
              onChange={(e) => setTestDate(e.target.value)}
              className="mt-1 w-full border border-line px-3 py-2 bg-paper font-mono-num text-sm focus:outline-none focus:border-navy"
            />
          </label>

          <label className="block">
            <span className="text-xs font-medium text-ink-soft uppercase tracking-wide">
              Raw Value {selectedActivity && `(${selectedActivity.unit})`}
            </span>
            <input
              type="number"
              step="0.01"
              required
              value={rawValue}
              onChange={(e) => setRawValue(e.target.value)}
              className="mt-1 w-full border border-line px-3 py-2 bg-paper font-mono-num text-sm focus:outline-none focus:border-navy"
              placeholder={selectedActivity ? "e.g. 26.5" : "Select an activity first"}
            />
          </label>
        </div>

        {error && (
          <div className="text-sm text-signal bg-signal-soft border border-signal/30 px-3 py-2">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={submitting || !traineeId || !activityId}
          className="bg-navy text-white font-medium px-5 py-2.5 hover:bg-navy-dark transition-colors disabled:opacity-50"
        >
          {submitting ? "Recording…" : "Record result"}
        </button>
      </form>

      {result && (
        <div className="mt-6 border border-line bg-white p-5 flex items-center justify-between">
          <div>
            <div className="text-xs text-ink-soft uppercase tracking-wide">
              Recorded
            </div>
            <div className="font-mono-num text-lg">{result.raw_value}</div>
          </div>
          <span
            className={`px-3 py-1 text-xs font-medium uppercase tracking-wide ${
              GRADE_STYLES[result.computed_grade ?? "fail"]
            }`}
          >
            {result.computed_grade ?? "Not applicable"}
          </span>
        </div>
      )}
    </div>
  );
}
