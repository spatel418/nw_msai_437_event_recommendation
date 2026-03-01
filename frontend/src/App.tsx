import { Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar";
import AdminPage from "./pages/AdminPage";
import NewUserPage from "./pages/NewUserPage";

export default function App() {
  return (
    <div className="min-h-screen bg-gray-950">
      <Navbar />
      <Routes>
        <Route path="/" element={<NewUserPage />} />
        <Route path="/admin" element={<AdminPage />} />
      </Routes>
    </div>
  );
}
