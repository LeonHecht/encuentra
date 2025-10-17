// src/routes/Chat.tsx
import { useEffect, useRef, useState } from "react";
import SpaceSelect from "@/components/SpaceSelect";

// AI Elements
import {
  Message,
  MessageContent,
} from "@/components/ai-elements/message";
import { Response } from "@/components/ai-elements/response";
import {
  PromptInput,
  PromptInputBody,
  PromptInputFooter,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputTools,
} from "@/components/ai-elements/prompt-input";

type Msg = {
  id: string;
  role: "user" | "assistant";
  text: string;
  citations?: any[];
};

export default function Chat() {
  const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

  // basic state
  const [messages, setMessages] = useState<Msg[]>([]);
  const [text, setText] = useState("");
  const [space, setSpace] = useState("supreme_court");
  const [agentState, setAgentState] = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "in_progress">("idle");

  // measure input bar height for the spacer
  const inputWrapRef = useRef<HTMLDivElement>(null);
  const [inputH, setInputH] = useState(96); // fallback

  useEffect(() => {
    const el = inputWrapRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setInputH(el.offsetHeight || 96));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // helper
  const token = (() => {
    try {
      const raw = localStorage.getItem("auth");
      return raw ? JSON.parse(raw).token : null;
    } catch {
      return null;
    }
  })();

  function pushMessage(role: "user" | "assistant", text: string, citations?: any[]) {
    setMessages((prev) => [
      ...prev,
      { id: `${Date.now()}-${prev.length}`, role, text, citations },
    ]);
    // keep the viewport pinned to bottom
    requestAnimationFrame(() =>
      window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" })
    );
  }

  async function handleSubmit(e?: React.FormEvent) {
    e?.preventDefault();
    const content = text.trim();
    if (!content || status === "in_progress") return;

    // optimistic append of user message
    pushMessage("user", content);
    setText("");
    setStatus("in_progress");

    try {
      const res = await fetch(`${API_BASE}/v1/chat/agentic`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          space,
          messages: [{ role: "user", content }],
          state: agentState || null,
        }),
      });

      if (!res.ok) throw new Error(`agentic ${res.status}`);
      const data = await res.json();

      if (data.agent_state) setAgentState(data.agent_state);
      pushMessage("assistant", data.answer || "", data.citations || []);
    } catch (err) {
      console.error("agentic error", err);
      pushMessage("assistant", "Ocurrió un error procesando tu consulta.");
    } finally {
      setStatus("idle");
    }
  }

  return (
    <div className="w-full">
      {/* page content column */}
      <div className="max-w-3xl mx-auto px-4 pt-4">
        {/* space picker */}
        <div className="mb-4">
          <SpaceSelect
            value={space}
            onChange={(v: string) => setSpace(v)}
            className="p-3 bg-transparent border border-transparent rounded-2xl hover:bg-gray-50 transition"
          />
        </div>

        {/* messages list (no internal scrolling!) */}
        <div className="space-y-4">
          {messages.map((m) => (
            <Message key={m.id} from={m.role}>
              <MessageContent>
                <Response>{m.text}</Response>
              </MessageContent>
            </Message>
          ))}
          {/* spacer so the fixed input never overlaps the last bubble */}
          <div style={{ height: inputH + 24 }} className="pointer-events-none" />
        </div>
      </div>

      {/* FIXED input bar pinned to viewport bottom */}
      <div
        ref={inputWrapRef}
        className="fixed bottom-0 left-0 right-0 z-50 border-t bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60"
      >
        <div className="max-w-3xl mx-auto px-4 py-2">
          <PromptInput onSubmit={handleSubmit}>
            <PromptInputBody>
              <PromptInputTextarea
                placeholder="Pregunta lo que quieras a tu asistente legal…"
                value={text}
                onChange={(e) => setText(e.target.value)}
              />
            </PromptInputBody>
            <PromptInputFooter>
              <PromptInputTools />
              <PromptInputSubmit
                disabled={!text || status === "in_progress"}
                status={status === "in_progress" ? "in_progress" : "idle"}
              />
            </PromptInputFooter>
          </PromptInput>
        </div>
      </div>
    </div>
  );
}
