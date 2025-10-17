import { useEffect, useState } from "react";
import SpaceSelect from "@/components/SpaceSelect";

// AI Elements
import { Conversation, ConversationContent } from "@/components/ai-elements/conversation";
import { Message, MessageContent } from "@/components/ai-elements/message";
import { Response } from "@/components/ai-elements/response";
import { PromptInput } from "@/components/ai-elements/prompt-input";
import { Reasoning } from "@/components/ai-elements/reasoning";
import { Sources } from "@/components/ai-elements/sources";
import { Loader } from "@/components/ai-elements/loader";

type ChatRole = "user" | "assistant";
type ChatMsg = { role: ChatRole; content: string; citations?: Array<{ doc_id: string; snippet?: string }>; };

type TraceEvent =
  | { type: "reasoning"; step: number; message: string; kind?: string }
  | { type: "tool_start"; step: number; tool: string; args?: unknown }
  | { type: "tool_result"; step: number; tool: string; result_count?: number }
  | { type: "final"; step: number; message?: string };

export default function Chat() {
  const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

  const [spaces, setSpaces] = useState<string[]>([]);
  const [space, setSpace] = useState<string>("");
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  // agentState es la cinta opaca que devuelve el backend para el siguiente turno
  const [agentState, setAgentState] = useState<string | null>(null);

  // razonamiento / trazas por turno más reciente
  const [lastTrace, setLastTrace] = useState<TraceEvent[] | null>(null);

  const token = (() => {
    try {
      const raw = localStorage.getItem("auth");
      return raw ? JSON.parse(raw).token as string : null;
    } catch {
      return null;
    }
  })();

  useEffect(() => {
    // carga de espacios
    fetch(`${API_BASE}/v1/user/spaces`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      credentials: "include",
    })
      .then((r) => r.json())
      .then((d) => {
        const s = d.spaces || [];
        setSpaces(s);
        if (s.length) setSpace(s[0]);
      })
      .catch((e) => console.error("Failed to fetch spaces", e));
  }, [API_BASE, token]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || !space) return;

    // pinta el mensaje del usuario
    const userMsg: ChatMsg = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    setLastTrace(null);

    try {
      const res = await fetch(`${API_BASE}/v1/chat/agentic`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: "include",
        body: JSON.stringify({
          space,
          // enviamos solo el último mensaje (tu backend ya mantiene estado con agent_state)
          messages: [{ role: "user", content: text }],
          state: agentState, // puede ser null en el primer turno
        }),
      });

      if (!res.ok) throw new Error(`agentic ${res.status}`);

      const data = await res.json() as {
        answer?: string;
        citations?: Array<{ doc_id: string; snippet?: string }>;
        trace?: TraceEvent[];
        agent_state?: string;
      };

      if (data.agent_state) setAgentState(data.agent_state);
      if (data.trace) setLastTrace(data.trace);

      const botMsg: ChatMsg = {
        role: "assistant",
        content: data.answer || "",
        citations: data.citations || [],
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      console.error("agentic error", err);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Ocurrió un error procesando tu consulta." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-full w-full max-w-3xl mx-auto px-4 py-4 gap-4">
      {/* Selector de espacio */}
      <div className="flex items-center gap-3">
        <SpaceSelect
          value={space}
          onChange={(v) => setSpace(v)}
          className="p-3 bg-transparent transition border border-input rounded-2xl hover:bg-muted/40"
          options={spaces}
        />
      </div>

      {/* Conversación */}
      <Conversation>
        <ConversationContent>
          {messages.map((m, idx) => (
            <Message key={idx} from={m.role}>
              <MessageContent>
                <Response>{m.content}</Response>

                {/* Si el último mensaje del assistant trae reasoning trace, muéstralo debajo */}
                {idx === messages.length - 1 && lastTrace && lastTrace.length > 0 && (
                  <div className="mt-3">
                    <Reasoning isStreaming={false} defaultOpen={false} title="Razonamiento">
                      <div className="space-y-2 text-sm text-muted-foreground">
                        {lastTrace.map((t, i) => {
                          if (t.type === "reasoning") {
                            return (
                              <div key={i}>
                                <span className="font-medium">Paso {t.step}:</span> {t.message}
                                {t.kind ? <span className="opacity-70"> ({t.kind})</span> : null}
                              </div>
                            );
                          }
                          if (t.type === "tool_start") {
                            return (
                              <div key={i}>
                                <span className="font-medium">Herramienta</span> «{t.tool}» iniciada (paso {t.step})
                              </div>
                            );
                          }
                          if (t.type === "tool_result") {
                            return (
                              <div key={i}>
                                <span className="font-medium">Resultado</span> «{t.tool}» — {t.result_count ?? 0} items
                              </div>
                            );
                          }
                          if (t.type === "final") {
                            return (
                              <div key={i}>
                                <span className="font-medium">Finalizado</span> (paso {t.step})
                              </div>
                            );
                          }
                          return null;
                        })}
                      </div>
                    </Reasoning>
                  </div>
                )}

                {/* Citas si existen */}
                {m.citations && m.citations.length > 0 && (
                  <div className="mt-3">
                    <Sources defaultOpen={false} title="Fuentes">
                      <ul className="list-disc pl-5 text-sm">
                        {m.citations.map((c, i) => (
                          <li key={i}>
                            <code className="px-1 py-0.5 rounded bg-muted">{c.doc_id}</code>
                            {c.snippet ? <> — <span className="opacity-80">{c.snippet}</span></> : null}
                          </li>
                        ))}
                      </ul>
                    </Sources>
                  </div>
                )}
              </MessageContent>
            </Message>
          ))}

          {loading && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground pl-3">
              <Loader /> Pensando…
            </div>
          )}
        </ConversationContent>

        {/* Input */}
        <form onSubmit={onSubmit} className="mt-2">
          <PromptInput
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Pregunta lo que quieras a tu asistente legal…"
            disabled={loading}
            onSubmit={onSubmit}
          />
        </form>
      </Conversation>
    </div>
  );
}
