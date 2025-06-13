import { Link } from "react-router-dom";

export default function Landing() {
  return (
    <div className="flex-1 h-screen flex flex-col items-center justify-center bg-gradient-to-b from-slate-50 to-slate-100">
      <h1 className="text-5xl font-extrabold mb-4">encuentra</h1>
      <p className="text-lg text-slate-700 mb-6">
        Instant legal search & chat over your documents
      </p>

      <div className="space-x-4">
        <Link
          to="/search"
          className="px-6 py-3 bg-teal-600 text-white rounded-lg hover:bg-teal-700"
        >
          🔍 Search
        </Link>
        <Link
          to="/chat"
          className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
        >
          💬 Chat
        </Link>
      </div>
    </div>
  );
}
