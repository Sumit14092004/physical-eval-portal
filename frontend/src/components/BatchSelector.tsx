import { useEffect, useState } from "react";
import { api } from "../api/client";

export interface Batch {
  id: string;
  name: string;
  start_date: string;
  end_date: string | null;
}

export function useBatches() {
  const [batches, setBatches] = useState<Batch[]>([]);
  const [selectedBatchId, setSelectedBatchId] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<Batch[]>("/org/batches")
      .then((res) => {
        setBatches(res.data);
        if (res.data.length > 0) setSelectedBatchId(res.data[0].id);
      })
      .finally(() => setLoading(false));
  }, []);

  return { batches, selectedBatchId, setSelectedBatchId, loading };
}

export function BatchSelector({
  batches,
  value,
  onChange,
}: {
  batches: Batch[];
  value: string;
  onChange: (id: string) => void;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="border border-line px-3 py-2 bg-white text-sm font-mono-num focus:outline-none focus:border-navy"
    >
      {batches.length === 0 && <option value="">No batches yet</option>}
      {batches.map((b) => (
        <option key={b.id} value={b.id}>
          {b.name}
        </option>
      ))}
    </select>
  );
}
