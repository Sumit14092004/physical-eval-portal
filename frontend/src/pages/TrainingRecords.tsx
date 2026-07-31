import { useEffect, useState, type FormEvent } from "react";
import { api } from "../api/client";
import { useBatches, BatchSelector } from "../components/BatchSelector";
import { useTrainees, TraineeSelect } from "../components/TraineeSelect";

interface TrainingRecordOut {
  id: string;
  subject_name: string;
  instructor_name: string;
  indoor_outdoor: "indoor" | "outdoor";
  periods_attended: number;
  periods_total: number;
  drill_performance: string | null;
  pt_performance: string | null;
  weapon_training: string | null;
  firing_practice: string | null;
  obstacle_training: string | null;
  tactical_training: string | null;
  created_at: string;
}

const emptyForm = {
  subjectName: "",
  instructorName: "",
  indoorOutdoor: "indoor" as "indoor" | "outdoor",
  periodsAttended: "",
  periodsTotal: "",
  practicalPerformance: "",
  bpetPptPerformance: "",
  drillPerformance: "",
  ptPerformance: "",
  weaponTraining: "",
  firingPractice: "",
  obstacleTraining: "",
  tacticalTraining: "",
};

export default function TrainingRecords() {
  const { batches, selectedBatchId, setSelectedBatchId } = useBatches();
  const { trainees } = useTrainees(selectedBatchId);
  const [traineeId, setTraineeId] = useState("");
  const [form, setForm] = useState(emptyForm);
  const [records, setRecords] = useState<TrainingRecordOut[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => setTraineeId(""), [selectedBatchId]);

  const loadRecords = (tid: string) => {
    if (!tid) {
      setRecords([]);
      return;
    }
    api.get<TrainingRecordOut[]>(`/training-records/${tid}`).then((res) => setRecords(res.data));
  };

  useEffect(() => loadRecords(traineeId), [traineeId]);

  const update = (field: keyof typeof emptyForm, value: string) =>
    setForm((f) => ({ ...f, [field]: value }));

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.post("/training-records", {
        trainee_id: traineeId,
        subject_name: form.subjectName,
        instructor_name: form.instructorName,
        indoor_outdoor: form.indoorOutdoor,
        periods_attended: parseInt(form.periodsAttended || "0", 10),
        periods_total: parseInt(form.periodsTotal || "0", 10),
        practical_performance: form.practicalPerformance || null,
        bpet_ppt_performance: form.bpetPptPerformance || null,
        drill_performance: form.drillPerformance || null,
        pt_performance: form.ptPerformance || null,
        weapon_training: form.weaponTraining || null,
        firing_practice: form.firingPractice || null,
        obstacle_training: form.obstacleTraining || null,
        tactical_training: form.tacticalTraining || null,
      });
      setForm(emptyForm);
      loadRecords(traineeId);
    } catch {
      setError("Couldn't save this training record. Please check the inputs and try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const textField = (
    label: string,
    field: keyof typeof emptyForm,
    placeholder?: string
  ) => (
    <label className="block">
      <span className="text-xs font-medium text-ink-soft uppercase tracking-wide">{label}</span>
      <input
        value={form[field]}
        onChange={(e) => update(field, e.target.value)}
        className="mt-1 w-full border border-line px-3 py-2 bg-paper text-sm focus:outline-none focus:border-navy"
        placeholder={placeholder}
      />
    </label>
  );

  return (
    <div className="p-8 max-w-2xl">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <div className="font-mono-num text-xs tracking-widest text-gold mb-1">MODULE 13</div>
          <h1 className="font-display font-bold text-2xl text-ink">Training Records</h1>
        </div>
        <BatchSelector batches={batches} value={selectedBatchId} onChange={setSelectedBatchId} />
      </div>

      <div className="bg-white border border-line p-6 mb-4">
        <label className="block mb-4">
          <span className="text-xs font-medium text-ink-soft uppercase tracking-wide">Trainee</span>
          <TraineeSelect trainees={trainees} value={traineeId} onChange={setTraineeId} />
        </label>
      </div>

      <form onSubmit={handleSubmit} className="bg-white border border-line p-6 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          {textField("Subject Name", "subjectName", "e.g. Field Craft")}
          {textField("Instructor Name", "instructorName", "e.g. Hav. Ramesh Yadav")}
        </div>

        <div className="grid grid-cols-3 gap-4">
          <label className="block">
            <span className="text-xs font-medium text-ink-soft uppercase tracking-wide">Type</span>
            <select
              value={form.indoorOutdoor}
              onChange={(e) => update("indoorOutdoor", e.target.value)}
              className="mt-1 w-full border border-line px-3 py-2 bg-paper text-sm focus:outline-none focus:border-navy"
            >
              <option value="indoor">Indoor</option>
              <option value="outdoor">Outdoor</option>
            </select>
          </label>
          <label className="block">
            <span className="text-xs font-medium text-ink-soft uppercase tracking-wide">Periods Attended</span>
            <input
              type="number"
              value={form.periodsAttended}
              onChange={(e) => update("periodsAttended", e.target.value)}
              className="mt-1 w-full border border-line px-3 py-2 bg-paper font-mono-num text-sm focus:outline-none focus:border-navy"
            />
          </label>
          <label className="block">
            <span className="text-xs font-medium text-ink-soft uppercase tracking-wide">Periods Total</span>
            <input
              type="number"
              value={form.periodsTotal}
              onChange={(e) => update("periodsTotal", e.target.value)}
              className="mt-1 w-full border border-line px-3 py-2 bg-paper font-mono-num text-sm focus:outline-none focus:border-navy"
            />
          </label>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {textField("Practical Performance", "practicalPerformance")}
          {textField("BPET & PPT Performance", "bpetPptPerformance")}
        </div>
        <div className="grid grid-cols-2 gap-4">
          {textField("Drill Performance", "drillPerformance")}
          {textField("PT Performance", "ptPerformance")}
        </div>
        <div className="grid grid-cols-2 gap-4">
          {textField("Weapon Training", "weaponTraining")}
          {textField("Firing Practice", "firingPractice")}
        </div>
        <div className="grid grid-cols-2 gap-4">
          {textField("Obstacle Training", "obstacleTraining")}
          {textField("Tactical Training", "tacticalTraining")}
        </div>

        {error && (
          <div className="text-sm text-signal bg-signal-soft border border-signal/30 px-3 py-2">{error}</div>
        )}

        <button
          type="submit"
          disabled={submitting || !traineeId}
          className="bg-navy text-white font-medium px-5 py-2.5 hover:bg-navy-dark transition-colors disabled:opacity-50"
        >
          {submitting ? "Saving…" : "Save training record"}
        </button>
      </form>

      {records.length > 0 && (
        <div className="mt-6 bg-white border border-line">
          <div className="px-5 py-3 text-xs uppercase tracking-wide text-ink-soft border-b border-line font-medium">
            Recorded entries for this trainee
          </div>
          {records.map((r) => (
            <div key={r.id} className="register-row px-5 py-3">
              <div className="flex justify-between items-baseline">
                <span className="text-sm font-medium">{r.subject_name}</span>
                <span className="font-mono-num text-xs text-ink-soft uppercase">{r.indoor_outdoor}</span>
              </div>
              <div className="text-xs text-ink-soft">
                {r.instructor_name} &middot; {r.periods_attended}/{r.periods_total} periods
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
