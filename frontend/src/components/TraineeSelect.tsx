import { useEffect, useState } from "react";
import { api } from "../api/client";

export interface TraineeOption {
  id: string;
  full_name: string;
  enrollment_number: string;
}

export function useTrainees(batchId: string) {
  const [trainees, setTrainees] = useState<TraineeOption[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!batchId) {
      setTrainees([]);
      return;
    }
    setLoading(true);
    api
      .get<TraineeOption[]>("/org/trainees", { params: { batch_id: batchId } })
      .then((res) => setTrainees(res.data))
      .finally(() => setLoading(false));
  }, [batchId]);

  return { trainees, loading };
}

export function TraineeSelect({
  trainees,
  value,
  onChange,
}: {
  trainees: TraineeOption[];
  value: string;
  onChange: (id: string) => void;
}) {
  return (
    <select
      required
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="mt-1 w-full border border-line px-3 py-2 bg-paper text-sm focus:outline-none focus:border-navy"
    >
      <option value="" disabled>
        {trainees.length === 0 ? "No trainees in this batch" : "Select a trainee…"}
      </option>
      {trainees.map((t) => (
        <option key={t.id} value={t.id}>
          {t.enrollment_number} — {t.full_name}
        </option>
      ))}
    </select>
  );
}
