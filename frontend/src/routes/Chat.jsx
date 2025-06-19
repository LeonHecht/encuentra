import { useState, useEffect } from "react";
import { useApi } from "@/hooks/useApi";
import SpaceSelect from "@/components/SpaceSelect";
import TypewriterText from "@/components/TypewriterText";

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
        <SpaceSelect
         value={space}
         onChange={(v) => setSpace(v)}
         className="p-3 bg-transparent transition border border-transparent rounded-2xl hover:border-inherit hover:bg-gray-50 hover:cursor-pointer focus:outline-none"
       />
      </div>

      {/* Chat window */}
      <div className="w-full flex-1 overflow-y-auto min-h-0 space-y-4 pr-1 pb-4">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`p-4 rounded-3xl ${
              m.role === "user" ? "bg-gray-100 self-end" : "bg-white hover:bg-gray-50 border transition"
            }`}
          >
          <p>
            {m.role === "bot"
              ? <TypewriterText text={m.text} />
              : m.text}                           
          </p>
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
        <div className={`input-wrapper flex-grow relative ${question ? 'caret-hidden' : ''}`}>
          <input
            type="text"
            className="flex-grow w-full py-3 px-4 border rounded-2xl
                                focus:outline-none focus:placeholder-transparent
                                hover:bg-gray-50 transition-colors"
            placeholder="Pregunta lo que quieras a tu asistente legal…"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
        </div>
        <button
          type="submit"
          className="px-8 py-3 bg-gray-200 text-gray-900 border rounded-3xl hover:bg-gray-300 transition"
          disabled={loading}
        >
          Enviar
        </button>
      </form>
    </div>
  );
}
