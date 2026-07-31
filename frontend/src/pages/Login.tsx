import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import type { AuthSession } from "../types";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const form = new URLSearchParams();
      form.append("username", email);
      form.append("password", password);
      const { data } = await api.post<AuthSession>("/auth/login", form, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      login(data.access_token, data.role, data.full_name);
      navigate("/");
    } catch {
      setError("Incorrect email or password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-paper">
      <div className="bg-navy-dark text-white/80 text-xs">
        <div className="max-w-6xl mx-auto px-6 py-1.5">
          Government Training Establishment &mdash; Physical Evaluation Portal
        </div>
      </div>
      <header className="bg-navy text-white">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center gap-3">
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
      </header>
      <div className="tricolor-stripe" />

      <div className="flex-1 flex items-center justify-center px-4 py-16">
        <div className="w-full max-w-sm">
          <div className="text-center mb-6">
            <h1 className="font-display font-bold text-2xl text-ink">
              Sign in to your account
            </h1>
            <p className="text-ink-soft text-sm mt-1">
              Access training, evaluation, and merit records.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="bg-white border border-line p-8 shadow-sm">
            <label className="block mb-4">
              <span className="text-xs font-medium text-ink-soft uppercase tracking-wide">
                Email
              </span>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 w-full border border-line px-3 py-2 bg-paper focus:outline-none focus:border-navy focus:ring-1 focus:ring-navy"
                placeholder="name@academy.test"
              />
            </label>

            <label className="block mb-6">
              <span className="text-xs font-medium text-ink-soft uppercase tracking-wide">
                Password
              </span>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 w-full border border-line px-3 py-2 bg-paper focus:outline-none focus:border-navy focus:ring-1 focus:ring-navy"
                placeholder="••••••••"
              />
            </label>

            {error && (
              <div className="mb-4 text-sm text-signal bg-signal-soft border border-signal/30 px-3 py-2">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-navy text-white font-medium py-2.5 hover:bg-navy-dark transition-colors disabled:opacity-50"
            >
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <p className="text-center text-xs text-ink-soft mt-4">
            Demo accounts use password <code className="font-mono-num bg-paper-dim px-1 py-0.5">Academy@2026</code> after seeding.
          </p>
        </div>
      </div>
    </div>
  );
}
