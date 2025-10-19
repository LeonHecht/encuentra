import { useEffect, useRef, useState } from "react";
import SpaceSelect from "@/components/SpaceSelect";
import { useApi } from "@/hooks/useApi";

// AI Elements
import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import { Message, MessageContent } from "@/components/ai-elements/message";
import { Response } from "@/components/ai-elements/response";
import {
  PromptInput,
  PromptInputBody,
  PromptInputTextarea,
  PromptInputFooter,
  PromptInputTools,
  PromptInputSubmit,
} from "@/components/ai-elements/prompt-input";

type ChatMsg = {
  id: string;
  role: "user" | "assistant";
  text: string;
  citations?: Array<{ doc_id: string; snippet?: string }>;
};

export default function Chat() {
  const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [spaces, setSpaces] = useState<string[]>([]);
  const [space, setSpace] = useState<string>("");
  const [agentState, setAgentState] = useState<string | null>(null);
  const [text, setText] = useState<string>("");
  const [status, setStatus] = useState<"ready" | "submitted" | "streaming">(
    "ready"
  );
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const token = (() => {
    try {
      const raw = localStorage.getItem("auth");
      return raw ? (JSON.parse(raw).token as string) : null;
    } catch {
      return null;
    }
  })();

  useEffect(() => {
    let alive = true;
    useApi("user/spaces")
      .then((d) => {
        if (!alive) return;
        const s: string[] = d.spaces || [];
        setSpaces(s);
        if (s.length > 0) setSpace((prev) => prev || s[0]);
      })
      .catch((e) => console.error("Failed to fetch spaces", e));
    return () => {
      alive = false;
    };
  }, []);

  function pushMessage(
    role: "user" | "assistant",
    text: string,
    citations?: ChatMsg["citations"]
  ) {
    setMessages((prev) => [
      ...prev,
      { id: `${Date.now()}-${prev.length}`, role, text, citations },
    ]);
  }

  async function handleSubmit() {
    const trimmed = text.trim();
    if (!trimmed || status !== "ready") return;

    pushMessage("user", trimmed);
    setText("");
    setStatus("submitted");

    try {
      const res = await fetch(`${API_BASE}/v1/chat/agentic`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          space,
          messages: [{ role: "user", content: trimmed }],
          state: agentState || null,
        }),
      });

      if (!res.ok) throw new Error(`agentic ${res.status}`);
      const data = await res.json();
      
      // Save the new agent_state for the next turn
      if (data.agent_state) setAgentState(data.agent_state);

      pushMessage("assistant", data.answer || "", data.citations || []);
    } catch (err) {
      console.error("agentic error", err);
      pushMessage("assistant", "Ocurrió un error procesando tu consulta.");
    } finally {
      setStatus("ready");
    }
  }

  return (
    <div className="h-full w-full flex flex-col">
      
      {/* Space selector - sticky below navbar */}
      <SpaceSelect
        value={space}
        onChange={(v) => setSpace(v)}
        className="sticky top-16 z-20 p-3 my-3 mx-auto bg-[#F5F5F7] border border-transparent rounded-2xl hover:bg-gray-50 self-start w-fit flex-none"
      />

      {/* Messages area - scrollable content */}
      <div className="flex-1 min-h-0">
        <div className="h-full overflow-y-auto">
          <div className="mx-auto max-w-4xl px-3 pb-24 pt-4">
            <Conversation>
              <ConversationContent>
                {messages.length === 0 ? (
                  <div className="flex items-center justify-center min-h-[60vh]">
                    <div className="text-center text-gray-600">
                      <div className="text-2xl">Hola, ¿cómo puedo ayudarte hoy?</div>
                    </div>
                  </div>
                ) : (
                  messages.map((m) => (
                    <Message key={m.id} from={m.role}>
                      <MessageContent>
                        <Response>{m.text}</Response>
                      </MessageContent>
                    </Message>
                  ))
                )}
              </ConversationContent>
              <ConversationScrollButton />
            </Conversation>
          </div>
        </div>
      </div>

      {/* Input fixed at bottom of screen */}
      <div className="fixed bottom-0 left-0 right-0 bg-[#F5F5F7] pb-3">
        <div className="mx-auto max-w-4xl px-3">
          <PromptInput onSubmit={handleSubmit} className="bg-white shadow-lg rounded-2xl">
            <PromptInputBody>
              <PromptInputTextarea
                ref={textareaRef}
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Pregunta lo que quieras a tu asistente legal…"
              />
            </PromptInputBody>
            <PromptInputFooter>
              <PromptInputTools />
              <PromptInputSubmit
                disabled={!text || status === 'submitted'}
                status={status}
              />
            </PromptInputFooter>
          </PromptInput>
        </div>
      </div>
    </div>
  );
}
