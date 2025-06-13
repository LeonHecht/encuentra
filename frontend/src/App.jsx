import { Routes, Route, Link } from "react-router-dom";
import Navbar from './components/Navbar';
import Landing from "./routes/Landing";
import Search from "./routes/Search";
import Chat from "./routes/Chat";
import Uploads from "./routes/Uploads";

export default function App() {
  return (
    <div className="flex flex-col min-h-screen bg-slate-50">
      <Navbar />
      <main className="flex-grow container mx-auto px-4 py-8">
        <Routes>
          <Route path="/"      element={<Landing />} />
          <Route path="/search"  element={<Search />} />
          <Route path="/chat"    element={<Chat />} />
          <Route path="/uploads" element={<Uploads />} />
        </Routes>
      </main>
      <footer className="bg-white text-center py-4 text-sm text-gray-500 border-t">
        © 2025 encuentra
      </footer>
    </div>
  );
}