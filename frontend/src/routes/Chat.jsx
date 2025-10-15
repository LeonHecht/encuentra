import { useState, useEffect } from "react";
import { useApi } from "@/hooks/useApi";
import SpaceSelect from "@/components/SpaceSelect";
import ChatMessage from "@/components/ChatMessage";

export default function Chat() {
  const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]); // {role,text,citations,file_url,streaming}
  const [spaces, setSpaces] = useState([]);
  const [space, setSpace] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    useApi("user/spaces")
      .then((d) => {
        const s = d.spaces || [];
        setSpaces(s);
        if (s.length > 0) setSpace(s[0]);
      })
      .catch((e) => console.error("Failed to fetch spaces", e));
  }, []);

  const askBot = (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    // 1) add user message
    const userMsg = { role: "user", text: question };
    setMessages((m) => [...m, userMsg]);
    setLoading(true);

    // 2) auth headers similar to useApi
    const raw = localStorage.getItem("auth");
    const token = raw ? JSON.parse(raw).token : null;
    // const headers = { "Content-Type": "application/json" };
    // if (token) headers["Authorization"] = `Bearer ${token}`;

    // 3) insert placeholder bot message; we'll set cumulative text as it streams
    setMessages((m) => [
      ...m,
      { role: "bot", text: "", citations: [], file_url: null, streaming: true },
    ]);

    const paramsObj = {
      space,
      messages: JSON.stringify(
        [...messages, { role: "user", text: question }].map(m => ({
          role: m.role === "bot" ? "assistant" : m.role,
          content: m.text ?? ""
        }))
      ),
      ...(token ? { token } : {}),
    };

    const params = new URLSearchParams(paramsObj);

    // If using cookie auth, pass { withCredentials: true }
    const es = new EventSource(`${API_BASE}/v1/chat/stream?${params.toString()}`);

    const close = () => {
      es.close();
      setLoading(false);
      setQuestion("");
    };

    es.addEventListener("content", (ev) => {
      const { delta } = JSON.parse(ev.data || "{}");
      if (typeof delta !== "string") return;
      setMessages((m) => {
        const copy = [...m];
        const last = copy[copy.length - 1];
        if (last?.role === "bot") {
          last.text = (last.text || "") + delta; // append tokens
        }
        return copy;
      });
    });

    es.addEventListener("done", (ev) => {
      try {
        const data = JSON.parse(ev.data || "{}");
        setMessages((m) => {
          const copy = [...m];
          const last = copy[copy.length - 1];
          if (last?.role === "bot") {
            last.text = data.answer ?? last.text ?? "";
            last.citations = data.citations || [];
            last.file_url = data.file_url || null;
            last.streaming = false;
          }
          return copy;
        });
      } catch {}
      close();
    });

    es.addEventListener("open", () => console.log("SSE open"));

    es.addEventListener("error", (e) => {
      console.error("SSE error", e);
      close();
    });
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
          <ChatMessage key={idx} msg={m} baseUrl={API_BASE} />
        ))}
        {loading && <p className="text-slate-500">Generando…</p>}
      </div>

      {/* Input */}
      <form onSubmit={askBot} className="flex-shrink-0 flex space-x-2">
        <div className={`input-wrapper flex-grow relative ${question ? "caret-hidden" : ""}`}>
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
