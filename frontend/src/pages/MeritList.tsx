import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useBatches, BatchSelector } from "../components/BatchSelector";
import { useAuth } from "../context/AuthContext";

interface MeritEntry {
  merit_position: number | null;
  trainee_id: string;
  trainee_name: string;
  enrollment_number: string;
  aggregate_marks: number;
  final_percentage: number;
}

export default function MeritList() {
  const { role } = useAuth();
  const isTrainee = role === "trainee";

  const { batches, selectedBatchId, setSelectedBatchId } = useBatches();
  const [ownTraineeId, setOwnTraineeId] = useState<string | null>(null);
  const [entries, setEntries] = useState<MeritEntry[]>([]);
  const [loading, setLoading] = useState(false);

  // Trainees don't get a batch picker -- their own batch resolves
  // automatically from their profile, same pattern as My Records.
  useEffect(() => {
    if (!isTrainee) return;
    api.get<{ id: string; batch_id: string }>("/org/trainees/me").then(({ data }) => {
      setOwnTraineeId(data.id);
      setSelectedBatchId(data.batch_id);
    });
  }, [isTrainee, setSelectedBatchId]);

  useEffect(() => {
    if (!selectedBatchId) return;
    setLoading(true);
    api
      .get<MeritEntry[]>("/exams/final/merit-list", { params: { batch_id: selectedBatchId } })
      .then((res) => setEntries(res.data))
      .finally(() => setLoading(false));
  }, [selectedBatchId]);

  return (
    <div className="p-8 max-w-3xl">
      <div className="mb-8 flex items-start justify-between">
        <div>
          <div className="font-mono-num text-xs tracking-widest text-gold mb-1">
            FINAL EXAMINATION — MERIT LIST
          </div>
          <h1 className="font-display text-3xl font-semibold text-ink">
            {isTrainee ? "Your Batch Merit Register" : "Batch Merit Register"}
          </h1>
        </div>
        {!isTrainee && (
          <BatchSelector batches={batches} value={selectedBatchId} onChange={setSelectedBatchId} />
        )}
      </div>

      {loading && <p className="text-ink-soft text-sm">Loading register…</p>}

      {!loading && entries.length === 0 && selectedBatchId && (
        <div className="border border-line bg-white p-6 text-sm text-ink-soft">
          No final examination results recorded for this batch yet.
        </div>
      )}

      {!loading && entries.length > 0 && (
        <div className="bg-white border border-line">
          <div className="grid grid-cols-[3rem_1fr_8rem_6rem_6rem] gap-4 px-5 py-3 text-xs uppercase tracking-wide text-ink-soft border-b border-line font-medium">
            <span>Rank</span>
            <span>Trainee</span>
            <span>Enrollment</span>
            <span className="text-right">Aggregate</span>
            <span className="text-right">%</span>
          </div>
          {entries.map((e) => (
            <div
              key={e.trainee_id}
              className={`register-row grid grid-cols-[3rem_1fr_8rem_6rem_6rem] gap-4 px-5 py-3 items-center ${
                e.trainee_id === ownTraineeId ? "bg-paper-dim" : ""
              }`}
            >
              <span className="font-mono-num text-gold font-semibold">
                {e.merit_position ?? "—"}
              </span>
              <span className="text-sm">
                {e.trainee_name}
                {e.trainee_id === ownTraineeId && (
                  <span className="ml-2 text-[10px] uppercase tracking-wide text-maroon font-medium">You</span>
                )}
              </span>
              <span className="font-mono-num text-xs text-ink-soft">
                {e.enrollment_number}
              </span>
              <span className="font-mono-num text-sm text-right">
                {e.aggregate_marks.toFixed(2)}
              </span>
              <span className="font-mono-num text-sm text-right">
                {e.final_percentage.toFixed(1)}%
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
