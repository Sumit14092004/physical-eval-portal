import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const CARDS = [
  { label: "My Records", to: "/my-records", desc: "Your physical evaluation, training, and exam results", roles: ["trainee"] },
  { label: "Training Records", to: "/training", desc: "Subject, instructor, drill & PT performance", roles: ["admin", "instructor"] },
  { label: "Physical Evaluation", to: "/physical-evaluation", desc: "BPET / PPT results, auto-graded", roles: ["admin", "instructor"] },
  { label: "Examinations", to: "/exams", desc: "Weekly, monthly, quarterly, final", roles: ["admin", "instructor"] },
  { label: "Merit List", to: "/merit", desc: "Batch-wide ranking register", roles: ["admin", "instructor", "trainee"] },
  { label: "Administration", to: "/admin", desc: "Create batches, add or import trainees", roles: ["admin"] },
];

export default function Dashboard() {
  const { fullName, role } = useAuth();

  return (
    <div className="p-8">
      <div className="mb-8">
        <div className="font-mono-num text-xs tracking-widest text-gold mb-1">
          {new Date().toLocaleDateString("en-IN", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
        </div>
        <h1 className="font-display text-3xl font-semibold text-ink">
          Welcome, {fullName ?? "—"}
        </h1>
        <p className="text-ink-soft text-sm mt-1">
          Signed in as <span className="uppercase font-mono-num text-xs">{role}</span>
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 max-w-2xl">
        {CARDS.filter((c) => role && c.roles.includes(role)).map((c) => (
          <Link
            key={c.to}
            to={c.to}
            className="bg-white border border-line p-5 hover:border-navy transition-colors"
          >
            <div className="font-display text-lg font-semibold text-ink">
              {c.label}
            </div>
            <div className="text-xs text-ink-soft mt-1">{c.desc}</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
