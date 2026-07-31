import { NavLink, Outlet, Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const NAV_ITEMS: { to: string; label: string; roles: string[] }[] = [
  { to: "/", label: "Dashboard", roles: ["admin", "instructor", "trainee"] },
  { to: "/my-records", label: "My Records", roles: ["trainee"] },
  { to: "/physical-evaluation", label: "Physical Evaluation", roles: ["admin", "instructor"] },
  { to: "/training", label: "Training Records", roles: ["admin", "instructor"] },
  { to: "/exams", label: "Examinations", roles: ["admin", "instructor"] },
  { to: "/merit", label: "Merit List", roles: ["admin", "instructor", "trainee"] },
  { to: "/admin", label: "Administration", roles: ["admin"] },
];

export default function AppShell() {
  const { isAuthenticated, role, fullName, logout } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) return <Navigate to="/login" replace />;

  const currentLabel =
    NAV_ITEMS.find((n) => n.to === location.pathname)?.label ?? "Dashboard";

  return (
    <div className="min-h-screen bg-paper flex flex-col">
      {/* Utility bar */}
      <div className="bg-navy-dark text-white/80 text-xs">
        <div className="max-w-6xl mx-auto px-6 py-1.5 flex items-center justify-between">
          <span>Government Training Establishment &mdash; Physical Evaluation Portal</span>
          <span className="font-mono-num tracking-wide">
            {new Date().toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}
          </span>
        </div>
      </div>

      {/* Main header */}
      <header className="bg-navy text-white">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-full bg-gold/90 flex items-center justify-center shrink-0">
              <span className="font-display font-black text-navy text-lg">PE</span>
            </div>
            <div>
              <div className="font-display font-bold text-lg leading-tight">
                Physical Evaluation Portal
              </div>
              <div className="text-[11px] text-white/60 tracking-wide">
                Training &middot; Examination &middot; Merit Register
              </div>
            </div>
          </div>

          <div className="text-right">
            <div className="text-sm font-medium">{fullName}</div>
            <div className="flex items-center gap-3 justify-end">
              <span className="font-mono-num text-[10px] uppercase tracking-widest text-gold">
                {role}
              </span>
              <button
                onClick={logout}
                className="text-[11px] text-white/70 hover:text-white transition-colors underline underline-offset-2"
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="tricolor-stripe" />

      {/* Horizontal nav */}
      <nav className="bg-white border-b border-line">
        <div className="max-w-6xl mx-auto px-6 flex">
          {NAV_ITEMS.filter((item) => role && item.roles.includes(role)).map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                  isActive
                    ? "border-maroon text-maroon"
                    : "border-transparent text-ink-soft hover:text-ink hover:border-line"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </div>
      </nav>

      {/* Breadcrumb */}
      <div className="bg-paper-dim border-b border-line">
        <div className="max-w-6xl mx-auto px-6 py-2 text-xs text-ink-soft">
          Home <span className="mx-1.5 text-line">/</span>
          <span className="text-ink font-medium">{currentLabel}</span>
        </div>
      </div>

      <main className="flex-1">
        <div className="max-w-6xl mx-auto w-full">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
