// frontend/src/routes/Search.jsx

import { useState, useEffect } from "react";
import { useApi } from "../hooks/useApi";


export default function Search() {
  const [q, setQ]           = useState("");
  const [spaces, setSpaces] = useState([]);
  const [space, setSpace]   = useState("");
  const [results, setResults] = useState([]);
  useEffect(() => {
    useApi("user/spaces").then((d) => {
      const s = d.spaces || [];
      setSpaces(s);
      if (s.length > 0) setSpace(s[0]);
    }).catch((e) => console.error("Failed to fetch spaces", e));
  }, []);

  const [loading, setLoading] = useState(false);
  const [feedbackById, setFeedbackById] = useState({});
  const [toast, setToast] = useState({ docId: null, msg: "" });

  // Highlight helper (same as in your other app)
  const renderSnippet = (snippet) => {
    const terms = Array.from(
      new Set(
        q
          .toLowerCase()
          .normalize("NFD")
          .replace(/[\u0300-\u036f]/g, "")
          .split(/[^A-Za-z]+/)
          .filter(Boolean)
      )
    );
    return snippet.split(" ").map((word, i) => {
      const ascii = word
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "");
      const clean = ascii.replace(/[^A-Za-z]/g, "").toLowerCase();
      if (terms.includes(clean)) {
        return (
          <strong key={i} className="font-bold">
            {word}{" "}
          </strong>
        );
      }
      return <span key={i}>{word} </span>;
    });
  };

  const onSearch = async () => {
    if (!q.trim()) return;
    setLoading(true);
    try {
      const res = await useApi(
        "search",
        `?q=${encodeURIComponent(q)}&space=${space}`
      );
      setResults(res.results || []);
    } catch (err) {
      console.error("Search error:", err);
      alert("Search failed. Check console.");
    } finally {
      setLoading(false);
    }
  };

  const sendFeedback = async (docId, positive) => {
    // stub: you'll wire this up to /feedback later
    setFeedbackById((f) => ({ ...f, [docId]: positive }));
    setToast({ docId, msg: positive ? "👍 Gracias!" : "👎 Gracias!" });
    setTimeout(() => setToast({ docId: null, msg: "" }), 2000);
  };

  return (
    <div className="w-full flex-1 overflow-y-auto min-h-0 space-y-4 px-16 py-8">
      <h2 className="text-2xl font-semibold mb-4">Buscar casos</h2>

      <div className="flex items-center mb-6 space-x-4">
        <select
          className="border p-2 rounded"
          value={space}
          onChange={(e) => setSpace(e.target.value)}
        >
          {spaces.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>

        <input
          type="text"
          className="flex-grow border p-2 rounded-l"
          placeholder="Palabra clave…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onSearch()}
        />
        <button
          onClick={onSearch}
          className="bg-teal-600 text-white p-2 rounded-r hover:bg-teal-700"
          disabled={loading}
        >
          {loading ? "Buscando..." : "Buscar"}
        </button>
      </div>

      <ul className="space-y-4">
        {results.map((res) => {
          const fb = feedbackById[res.id];
          const isToast = toast.docId === res.id;

          return (
            <li
              key={res.id}
              className="p-4 border rounded-lg hover:shadow flex flex-col"
            >
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold">{res.title}</h3>
                <span className="text-sm font-mono text-gray-500">
                  {res.id}
                </span>
              </div>
              <span className="text-sm font-semibold text-indigo-600">
                Score: {res.score.toFixed(3)}
              </span>

              <p className="mt-2 text-gray-700 text-sm">
                {renderSnippet(res.snippet)}
                {res.snippet.split(" ").length >= 50 ? "…" : ""}
              </p>

              <div className="mt-3 flex items-center space-x-2">
                {res.download_url && (
                  <a
                    href={res.download_url}
                    target="_blank"
                    rel="noreferrer"
                    className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-100"
                  >
                    Download Full Case
                  </a>
                )}

                <button
                  onClick={() => sendFeedback(res.id, true)}
                  disabled={fb != null}
                  className={`p-1 rounded-full transition ${
                    fb === true ? "bg-green-200 text-green-800" : "hover:bg-green-100 text-gray-600"
                  }`}
                >
                  👍
                </button>
                <button
                  onClick={() => sendFeedback(res.id, false)}
                  disabled={fb != null}
                  className={`p-1 rounded-full transition ${
                    fb === false ? "bg-red-200 text-red-800" : "hover:bg-red-100 text-gray-600"
                  }`}
                >
                  👎
                </button>
              </div>

              {isToast && (
                <div className="mt-2 text-sm text-gray-800">{toast.msg}</div>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
