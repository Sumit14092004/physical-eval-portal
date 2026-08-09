import { useState, type FormEvent } from "react";
import { api } from "../api/client";
import { useBatches, BatchSelector } from "../components/BatchSelector";

function SectionCard({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <div className="bg-white border border-line p-6 mb-6">
      <div className="mb-4">
        <h2 className="font-display font-bold text-lg text-ink">{title}</h2>
        <p className="text-xs text-ink-soft mt-0.5">{subtitle}</p>
      </div>
      {children}
    </div>
  );
}

function Field({
  label, value, onChange, type = "text", placeholder, required = true,
}: { label: string; value: string; onChange: (v: string) => void; type?: string; placeholder?: string; required?: boolean }) {
  return (
    <label className="block">
      <span className="text-xs font-medium text-ink-soft uppercase tracking-wide">{label}</span>
      <input
        type={type}
        required={required}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="mt-1 w-full border border-line px-3 py-2 bg-paper text-sm focus:outline-none focus:border-navy"
      />
    </label>
  );
}

// ---------- Create Batch ----------
function CreateBatchForm({ onCreated }: { onCreated: () => void }) {
  const [name, setName] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setStatus(null);
    setSubmitting(true);
    try {
      await api.post("/org/batches", {
        name, start_date: startDate, end_date: endDate || null,
      });
      setStatus("success");
      setName(""); setStartDate(""); setEndDate("");
      onCreated();
    } catch {
      setStatus("error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Field label="Batch Name" value={name} onChange={setName} placeholder="e.g. GD Constable Batch 2026-B" />
      <div className="grid grid-cols-2 gap-4">
        <Field label="Start Date" type="date" value={startDate} onChange={setStartDate} />
        <Field label="End Date" type="date" value={endDate} onChange={setEndDate} required={false} />
      </div>
      {status === "error" && (
        <div className="text-sm text-signal bg-signal-soft border border-signal/30 px-3 py-2">
          Couldn't create the batch. Please check the inputs.
        </div>
      )}
      {status === "success" && (
        <div className="text-sm text-indiagreen bg-paper-dim border border-line px-3 py-2">
          Batch created.
        </div>
      )}
      <button type="submit" disabled={submitting} className="bg-navy text-white font-medium px-5 py-2.5 hover:bg-navy-dark transition-colors disabled:opacity-50">
        {submitting ? "Creating…" : "Create batch"}
      </button>
    </form>
  );
}

// ---------- Add Single Trainee ----------
function AddTraineeForm({ batchId }: { batchId: string }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [enrollmentNumber, setEnrollmentNumber] = useState("");
  const [dob, setDob] = useState("");
  const [gender, setGender] = useState("Male");
  const [status, setStatus] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setStatus(null);
    setSubmitting(true);
    try {
      await api.post("/org/trainees", {
        email, password, full_name: fullName, batch_id: batchId,
        enrollment_number: enrollmentNumber, date_of_birth: dob, gender,
      });
      setStatus("success");
      setEmail(""); setPassword(""); setFullName(""); setEnrollmentNumber(""); setDob("");
    } catch {
      setStatus("error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <Field label="Full Name" value={fullName} onChange={setFullName} />
        <Field label="Enrollment Number" value={enrollmentNumber} onChange={setEnrollmentNumber} />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Email" type="email" value={email} onChange={setEmail} />
        <Field label="Temporary Password" type="text" value={password} onChange={setPassword} />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Date of Birth" type="date" value={dob} onChange={setDob} />
        <label className="block">
          <span className="text-xs font-medium text-ink-soft uppercase tracking-wide">Gender</span>
          <select value={gender} onChange={(e) => setGender(e.target.value)} className="mt-1 w-full border border-line px-3 py-2 bg-paper text-sm focus:outline-none focus:border-navy">
            <option>Male</option><option>Female</option><option>Other</option>
          </select>
        </label>
      </div>
      {status === "error" && (
        <div className="text-sm text-signal bg-signal-soft border border-signal/30 px-3 py-2">
          Couldn't add this trainee — check the email/enrollment number aren't already used.
        </div>
      )}
      {status === "success" && (
        <div className="text-sm text-indiagreen bg-paper-dim border border-line px-3 py-2">
          Trainee added to the selected batch.
        </div>
      )}
      <button type="submit" disabled={submitting || !batchId} className="bg-navy text-white font-medium px-5 py-2.5 hover:bg-navy-dark transition-colors disabled:opacity-50">
        {submitting ? "Adding…" : "Add trainee"}
      </button>
    </form>
  );
}

// ---------- Bulk CSV Import ----------
function BulkImportForm({ batchId }: { batchId: string }) {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<{ created: number; skipped: number; errors: { row: number; email: string | null; error: string }[] } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setError(null);
    setResult(null);
    setSubmitting(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await api.post(`/org/trainees/bulk-import?batch_id=${batchId}`, formData);
      setResult(data);
    } catch {
      setError("Import failed. Check the CSV has the required columns: email, password, full_name, enrollment_number, date_of_birth, gender.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="text-xs text-ink-soft bg-paper-dim border border-line px-3 py-2">
        Required CSV columns: <code className="font-mono-num">email, password, full_name, enrollment_number, date_of_birth (YYYY-MM-DD), gender</code>.
        Optional: <code className="font-mono-num">personnel_category</code>.
      </div>
      <input
        type="file"
        accept=".csv"
        onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        className="block w-full text-sm border border-line px-3 py-2 bg-paper"
      />
      {error && <div className="text-sm text-signal bg-signal-soft border border-signal/30 px-3 py-2">{error}</div>}
      <button type="submit" disabled={submitting || !file || !batchId} className="bg-navy text-white font-medium px-5 py-2.5 hover:bg-navy-dark transition-colors disabled:opacity-50">
        {submitting ? "Importing…" : "Import CSV"}
      </button>

      {result && (
        <div className="border border-line bg-paper-dim px-4 py-3 text-sm space-y-2">
          <div>
            <span className="font-mono-num text-indiagreen font-semibold">{result.created}</span> created,{" "}
            <span className="font-mono-num text-ink-soft">{result.skipped}</span> skipped (duplicates),{" "}
            <span className="font-mono-num text-signal">{result.errors.length}</span> errors
          </div>
          {result.errors.length > 0 && (
            <div className="max-h-40 overflow-y-auto space-y-1">
              {result.errors.map((err, i) => (
                <div key={i} className="text-xs text-signal font-mono-num">
                  Row {err.row}{err.email ? ` (${err.email})` : ""}: {err.error}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </form>
  );
}

export default function Admin() {
  const { batches, selectedBatchId, setSelectedBatchId, loading, refetch } = useBatches();

  return (
    <div className="p-8 max-w-2xl">
      <div className="mb-6">
        <div className="font-mono-num text-xs tracking-widest text-gold mb-1">ADMINISTRATION</div>
        <h1 className="font-display font-bold text-2xl text-ink">Batches & Trainees</h1>
        <p className="text-ink-soft text-sm mt-1">
          Create training batches, add individual trainees, or import in bulk via CSV.
        </p>
      </div>

      <SectionCard title="Create a Batch" subtitle="A training cohort — trainees, exams, and ranks are scoped to a batch.">
        <CreateBatchForm onCreated={refetch} />
      </SectionCard>

      <div className="mb-4 flex items-center justify-between">
        <span className="text-xs font-medium text-ink-soft uppercase tracking-wide">Working batch</span>
        <BatchSelector batches={batches} value={selectedBatchId} onChange={setSelectedBatchId} />
      </div>

      {!loading && batches.length === 0 && (
        <div className="border border-line bg-white p-4 text-sm text-ink-soft mb-6">
          Create a batch above before adding trainees.
        </div>
      )}

      <SectionCard title="Add a Single Trainee" subtitle="Creates a login and enrolls them in the selected batch above.">
        <AddTraineeForm batchId={selectedBatchId} />
      </SectionCard>

      <SectionCard title="Bulk Import Trainees" subtitle="Upload a CSV to onboard many trainees at once into the selected batch above.">
        <BulkImportForm batchId={selectedBatchId} />
      </SectionCard>
    </div>
  );
}
