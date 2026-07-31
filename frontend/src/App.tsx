import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import AppShell from "./components/AppShell";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import PhysicalEvaluation from "./pages/PhysicalEvaluation";
import TrainingRecords from "./pages/TrainingRecords";
import Examinations from "./pages/Examinations";
import MeritList from "./pages/MeritList";
import Admin from "./pages/Admin";
import MyRecords from "./pages/MyRecords";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter basename={import.meta.env.BASE_URL}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<AppShell />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/physical-evaluation" element={<PhysicalEvaluation />} />
            <Route path="/training" element={<TrainingRecords />} />
            <Route path="/exams" element={<Examinations />} />
            <Route path="/merit" element={<MeritList />} />
            <Route path="/admin" element={<Admin />} />
            <Route path="/my-records" element={<MyRecords />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
