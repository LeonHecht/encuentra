import { Navigate, Routes, Route } from "react-router-dom";
import Navbar from './components/Navbar';
import Landing from "./routes/Landing";
import Search from "./routes/Search";
import Chat from "./routes/Chat";
import AuthPage from "./routes/AuthPage";
import PrivacyPolicy from "./routes/PrivacyPolicy";
import TermsOfService from "./routes/TermsOfService";
// import bg from './assets/landing_bg.png';

export default function App() {
  return (
    <div className="flex flex-col h-dvh overflow-x-hidden">
      <Navbar />
      <main className="flex flex-col flex-1 min-h-0 bg-[#F5F5F7]">
        <Routes>
          <Route path="/"      element={<Landing />} />
          <Route path="/search"  element={<Search />} />
          <Route path="/chat"    element={<Chat />} />
          <Route path="/uploads" element={<Navigate to="/search" replace />} />
          <Route path="/login"   element={<AuthPage />} />
          <Route path="/signup"  element={<AuthPage initialView="sign_up" />} />
          <Route path="/privacy" element={<PrivacyPolicy />} />
          <Route path="/terms" element={<TermsOfService />} />
          <Route path="/privacy-policy" element={<Navigate to="/privacy" replace />} />
          <Route path="/terms-of-service" element={<Navigate to="/terms" replace />} />
        </Routes>
      </main>
      {/* <footer className="text-center py-1 text-xs text-gray-500 border-t">
        © 2025 encuentra
      </footer> */}
    </div>
  );
}
