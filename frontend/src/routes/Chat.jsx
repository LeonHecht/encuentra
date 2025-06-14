import { useState, useEffect } from "react";
import { useApi } from "../hooks/useApi";

export default function Chat() {
  const [question, setQuestion]   = useState("");
  const [messages, setMessages]   = useState([]); // {role,text,citations}
  const [spaces, setSpaces]       = useState([]);
  const [space, setSpace]         = useState("");
  useEffect(() => {
    useApi("user/spaces").then((d) => {
      const s = d.spaces || [];
      setSpaces(s);
      if (s.length > 0) setSpace(s[0]);
    }).catch((e) => console.error("Failed to fetch spaces", e));
  }, []);
  const [loading, setLoading]     = useState(false);

  const askBot = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    const userMsg = { role: "user", text: question };
    setMessages((m) => [...m, userMsg]);
    setLoading(true);

    const data = await useApi("chat", "", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, space }),
    });
    const botMsg = {
      role: "bot",
      text: data.answer,
      citations: data.citations,
    };
    setMessages((m) => [...m, botMsg]);
    setQuestion("");
    setLoading(false);
  };

  return (
    <div className="flex flex-col h-full w-full min-h-0 mx-auto px-4 py-4 max-w-2xl">
      {/* Context selector */}
      <div className="mb-4">
        <select
          value={space}
          onChange={(e) => setSpace(e.target.value)}
          className="border p-2 rounded"
        >
          {spaces.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      {/* Chat window */}
      <div className="w-full flex-1 overflow-y-auto min-h-0 space-y-4 pr-1 pb-4">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`p-3 rounded ${
              m.role === "user" ? "bg-slate-100 self-end" : "bg-white"
            }`}
          >
            <p>{m.text}</p>
            {m.citations && m.citations.length > 0 && (
              <div className="mt-2 text-xs text-slate-500">
                Fuente: {m.citations[0].doc_id}
              </div>
            )}
          </div>
        ))}
        {loading && <p className="text-slate-500">⌛ Generando…</p>}
      </div>

      {/* Input */}
      <form onSubmit={askBot} className="flex-shrink-0 flex space-x-2">
        <input
          type="text"
          className="flex-grow border p-2 rounded-l"
          placeholder="Pregunta…"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button
          type="submit"
          className="bg-indigo-600 text-white px-4 rounded-r hover:bg-indigo-700"
          disabled={loading}
        >
          Enviar
        </button>
      </form>
    </div>
  );
}
