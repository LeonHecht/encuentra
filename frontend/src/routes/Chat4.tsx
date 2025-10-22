import { useEffect, useRef, useState, useCallback } from "react";
import SpaceSelect from "@/components/SpaceSelect";
import ChatSidebar from "@/components/ChatSidebar";
import { useApi } from "@/hooks/useApi";
import { supabase } from "@/lib/supabaseClient";
import { SidebarProvider, SidebarTrigger, SidebarInset } from "@/components/ui/sidebar"

// AI Elements
import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import { Message, MessageContent } from "@/components/ai-elements/message";
import { Response } from "@/components/ai-elements/response";
import MarkdownWithCitations from "@/components/MarkdownWithCitations";
import {
  InlineCitation,
  InlineCitationText,
  InlineCitationCard,
  InlineCitationCardTrigger,
  InlineCitationCardBody,
  InlineCitationCarousel,
  InlineCitationCarouselHeader,
  InlineCitationCarouselIndex,
  InlineCitationCarouselPrev,
  InlineCitationCarouselNext,
  InlineCitationCarouselContent,
  InlineCitationCarouselItem,
  InlineCitationSource,
  InlineCitationQuote,
} from "@/components/ai-elements/inline-citation";
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
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
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
    citations: ChatMsg["citations"] = []
  ) {
    setMessages((prev) => [
      ...prev,
      { id: `${Date.now()}-${prev.length}`, role, text, citations },
    ]);
  }

  const loadChatMessages = useCallback(async (chatId: string) => {
    const { data, error } = await supabase
      .from("chat_messages")
      .select("id, role, content, meta")
      .eq("chat_id", chatId)
      .order("created_at", { ascending: true });

    if (!error && data) {
      setMessages(
        (data as any[]).map((m) => ({
          id: m.id,
          role: m.role,
          text: m.content as string,
          citations: m.meta?.citations || [],
        }))
      );
    }
  }, []);
  const loadChatAgentState = useCallback(async (chatId: string) => {
    const { data, error } = await supabase
      .from("chats")
      .select("agent_state")
      .eq("id", chatId)
      .single();

    if (!error && data) {
      const st = (data as any).agent_state;
      if (st == null) {
        setAgentState(null);
      } else if (typeof st === "string") {
        setAgentState(st);
      } else {
        try {
          setAgentState(JSON.stringify(st));
        } catch {
          setAgentState(null);
        }
      }
    }
  }, []);

  async function ensureChat(title: string) {
    if (currentChatId) return currentChatId;
    const {
      data: { user },
    } = await supabase.auth.getUser();
    if (!user) throw new Error("Necesitas iniciar sesión");

    const { data, error } = await supabase
      .from("chats")
      .insert({ user_id: user.id, title })
      .select()
      .single();
    if (error) throw error;

    setCurrentChatId(data.id as string);
    return data.id as string;
  }

  async function handleSubmit() {
    console.log("agent state:", agentState);
    
    const trimmed = text.trim();
    if (!trimmed || status !== "ready") return;

    setStatus("submitted");
    try {
      // Ensure we have a chat ID, creating one if needed
      const chatId = await ensureChat(trimmed.slice(0, 60));

      // Store user message (and also update local UI immediately)
      pushMessage("user", trimmed);
      setText("");
      const { error: insertUserErr } = await supabase.from("chat_messages").insert({
        chat_id: chatId,
        role: "user",
        content: trimmed,
        meta: null,
      });
      if (insertUserErr) {
        console.error("Failed to persist user message:", insertUserErr);
      }

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
      
      // Save the new agent_state for the next turn and persist it with the chat
      if (data.agent_state) {
        setAgentState(data.agent_state);
        try {
          await supabase
            .from("chats")
            .update({ agent_state: data.agent_state })
            .eq("id", chatId);
        } catch (e) {
          console.error("Failed to persist agent_state:", e);
        }
      }

      // Store assistant message
      const { error: insertAssistantErr } = await supabase.from("chat_messages").insert({
        chat_id: chatId,
        role: "assistant",
        content: data.answer || "",
        meta: { citations: data.citations || [] },
      });
      if (insertAssistantErr) {
        console.error("Failed to persist assistant message:", insertAssistantErr);
      }

      console.log("===Citations===");
      console.log(data.citations);

      pushMessage("assistant", data.answer || "", data.citations || []);
    } catch (err) {
      console.error("agentic submit error", err);
      pushMessage("assistant", "Ocurrió un error procesando tu consulta.");
    } finally {
      setStatus("ready");
    }
  }

  return (
    <SidebarProvider className="min-h-0 h-full w-full overflow-hidden">
      {/* Sidebar (fixed) + inset content. Using SidebarInset prevents double sidebar and handles the gap. */}
      <ChatSidebar
        className="shrink-0"
        selectedId={currentChatId}
        onSelect={(id) => {
          setCurrentChatId(id);
          loadChatMessages(id);
          loadChatAgentState(id);
        }}
        onCreated={(id) => {
          setCurrentChatId(id);
          setMessages([]);
          setAgentState(null);
        }}
      />

      {/* Main content inside the SidebarInset so it accounts for the sidebar gap */}
      <SidebarInset className="flex flex-col flex-1 min-h-0 min-w-0 overflow-hidden bg-[#F5F5F7]">
          {/* Sidebar toggle + Space selector (sticky below navbar) */}
          <div className="flex items-center gap-2 p-2">
            <SidebarTrigger />
            <SpaceSelect
              value={space}
              onChange={(v) => setSpace(v)}
              className="ml-1"
            />
          </div>

          {/* Messages area - scrollable content */}
          <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
            <div
              className={`flex-1 min-h-0 overflow-y-auto px-3 pt-2 ${
                messages.length > 0 ? "pb-24" : "pb-6"
              }`}
            >
              <div className="mx-auto w-full max-w-4xl">
              <Conversation>
                <ConversationContent>
                  {messages.length === 0 ? (
                    <div className="flex items-center justify-center min-h-[50vh]">
                      <div className="text-center text-2xl text-gray-600">
                        Hola, ¿cómo puedo ayudarte hoy?
                      </div>
                    </div>
                  ) : (
                    messages.map((m) => (
                      <Message key={m.id} from={m.role}>
                        <MessageContent>
                          {m.role === "assistant" ? (
                            <MarkdownWithCitations
                              className="prose prose-slate max-w-none"
                              text={m.text}
                              citations={m.citations || []}
                              apiBase={API_BASE}
                            />
                          ) : (
                            <Response>{m.text}</Response>
                          )}
                        </MessageContent>
                      </Message>
                    ))
                  )}
                </ConversationContent>
                <ConversationScrollButton />
              </Conversation>
              </div>
            </div>
            {/* Input fixed at bottom of screen */}
            {/* <Textarea className="bg-white w-full max-w-2xl mx-auto shrink-0" placeholder="Type your message here." /> */}
            {/* <div className="fixed bottom-0 left-0 right-0 bg-[#F5F5F7] pb-3"> */}
            <div className="mx-auto max-w-3xl w-full shrink-0 px-3 pb-3">
              <PromptInput
                onSubmit={handleSubmit}
                className="bg-white rounded-2xl shadow-lg transition-colors hover:bg-gray-50"
              >
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
                    disabled={!text || status === "submitted"}
                    status={status}
                  />
                </PromptInputFooter>
              </PromptInput>
            </div>
          </div>
      </SidebarInset>
      {/* </div> */}
    </SidebarProvider>
  );
}
