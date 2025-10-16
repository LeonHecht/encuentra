import { useState, useEffect, useRef } from "react";
import { useApi } from "@/hooks/useApi";
import SpaceSelect from "@/components/SpaceSelect";
import ChatMessage from "@/components/ChatMessage";

export default function Chat() {
  const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
  const [messages, setMessages] = useState([]); // {role,text,citations,file_url,streaming}
  const [question, setQuestion] = useState("");
  const [spaces, setSpaces] = useState([]);
  const [space, setSpace] = useState("");
  const [agentState, setAgentState] = useState(null); // opaque JSON string from backend
  const [loading, setLoading] = useState(false);
  const esRef = useRef(null);

  useEffect(() => {
    useApi("user/spaces")
      .then((d) => {
        const s = d.spaces || [];
        setSpaces(s);
        if (s.length > 0) setSpace(s[0]);
      })
      .catch((e) => console.error("Failed to fetch spaces", e));
    return () => esRef.current?.close();
  }, []);

  const token = (() => {
    try {
      const raw = localStorage.getItem("auth");
      return raw ? JSON.parse(raw).token : null;
    } catch { return null; }
  })();

  const toChatAPIFormat = (msgs) =>
    msgs.map(m => ({ role: m.role === "bot" ? "assistant" : m.role, content: m.text ?? "" }));

  async function sendStreaming(e) {
    e.preventDefault();
    if (!question.trim()) return;

    const userMsg = { role: "user", text: question };
    setMessages((m) => [...m, userMsg, { role: "bot", text: "", citations: [], file_url: null, streaming: true }]);
    setQuestion("");
    setLoading(true);

    const params = new URLSearchParams({
      space,
      messages: JSON.stringify(toChatAPIFormat([...messages, userMsg])),
      ...(token ? { token } : {}),
    });

    esRef.current?.close();
    const es = new EventSource(`${API_BASE}/v1/chat/stream?${params.toString()}`);
    esRef.current = es;

    es.addEventListener("open", () => console.log("SSE open"));

    es.addEventListener("content", (ev) => {
      const { delta } = JSON.parse(ev.data || "{}");
      if (typeof delta !== "string") return;
      setMessages((m) => {
        const copy = [...m];
        const last = copy[copy.length - 1];
        if (last?.role === "bot") last.text = (last.text || "") + delta;
        return copy;
      });
    });

    const close = () => {
      es.close();
      setLoading(false);
    };

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

    es.addEventListener("error", (e) => {
      console.error("SSE error", e);
      close();
    });
  }

  async function sendAgentic(e) {
    e.preventDefault();
    if (!question.trim()) return;

    const userMsg = { role: "user", text: question };
    const apiMsg = { role: "user", content: question };

    setMessages((m) => [...m, userMsg]);
    setQuestion("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/v1/chat/agentic`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          space,
          messages: [apiMsg], // just the last user msg
          state: agentState || null, // carry agent tape
        }),
      });

      if (!res.ok) throw new Error(`agentic ${res.status}`);
      
      const data = await res.json();
      
      // Save the new agent_state for the next turn
      if (data.agent_state) setAgentState(data.agent_state);
      
      setMessages((m) => [
        ...m,
        {
          role: "bot",
          text: data.answer || "",
          citations: data.citations || [],
          file_url: null,
          streaming: false,
        },
      ]);
    } catch (err) {
      console.error("agentic error", err);
      setMessages((m) => [...m, { role: "bot", text: "Ocurrió un error procesando tu consulta.", streaming: false }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-full w-full min-h-0 mx-auto px-4 py-4 max-w-2xl">
      <div className="mb-4">
        <SpaceSelect
          value={space}
          onChange={(v) => setSpace(v)}
          className="p-3 bg-transparent transition border border-transparent rounded-2xl hover:border-inherit hover:bg-gray-50 hover:cursor-pointer focus:outline-none"
        />
      </div>

      <div className="w-full flex-1 overflow-y-auto min-h-0 space-y-4 pr-1 pb-4">
        {messages.map((m, idx) => (
          <ChatMessage key={idx} msg={m} baseUrl={API_BASE} />
        ))}
        {loading && <p className="text-slate-500">Pensando para darte una mejor respuesta…</p>}
      </div>

      <form className="flex-shrink-0 flex gap-2" onSubmit={sendStreaming}>
        <input
          type="text"
          className="flex-grow w-full py-3 px-4 border rounded-2xl focus:outline-none hover:bg-gray-50 transition-colors"
          placeholder="Pregunta lo que quieras a tu asistente legal…"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        {/* Two buttons so you can test both backends */}
        <button type="submit" className="px-4 py-3 bg-gray-200 rounded-2xl" disabled={loading}>
          Stream
        </button>
        <button onClick={sendAgentic} className="px-4 py-3 bg-gray-300 rounded-2xl" disabled={loading}>
          Agentic
        </button>
      </form>
    </div>
  );
}
