import { createContext, useContext, useState, type ReactNode } from "react";
import type { UserRole } from "../types";

interface AuthState {
  role: UserRole | null;
  fullName: string | null;
  isAuthenticated: boolean;
  login: (token: string, role: UserRole, fullName: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [role, setRole] = useState<UserRole | null>(
    (localStorage.getItem("role") as UserRole) || null
  );
  const [fullName, setFullName] = useState<string | null>(
    localStorage.getItem("full_name")
  );

  const login = (token: string, role: UserRole, fullName: string) => {
    localStorage.setItem("access_token", token);
    localStorage.setItem("role", role);
    localStorage.setItem("full_name", fullName);
    setRole(role);
    setFullName(fullName);
  };

  const logout = () => {
    localStorage.clear();
    setRole(null);
    setFullName(null);
  };

  return (
    <AuthContext.Provider
      value={{ role, fullName, isAuthenticated: !!role, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
