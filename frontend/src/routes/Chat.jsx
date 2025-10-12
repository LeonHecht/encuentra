import { useEffect, useMemo, useRef, useState } from "react";
import { useChat } from "ai/react";
import { useApi } from "@/hooks/useApi";
import SpaceSelect from "@/components/SpaceSelect";
import ChatMessage from "@/components/ChatMessage";

const encoder = new TextEncoder();
const decoder = new TextDecoder("utf-8");

export default function Chat() {
  const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
  const [spaces, setSpaces] = useState([]);
  const [space, setSpace] = useState("");
  const lastAssistantMetaRef = useRef({ citations: [], file_url: null });

  useEffect(() => {
    useApi("user/spaces")
      .then((d) => {
        const s = d.spaces || [];
        setSpaces(s);
        if (s.length > 0) setSpace((curr) => curr || s[0]);
      })
      .catch((e) => console.error("Failed to fetch spaces", e));
  }, []);

  const body = useMemo(() => ({ space }), [space]);

  const {
    messages,
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    setMessages,
  } = useChat({
    api: `${API_BASE}/v1/chat/stream`,
    body,
    sendExtraMessageFields: true,
    fetch: async (_input, init) => {
      let rawBody = {};
      if (init?.body) {
        try {
          rawBody = JSON.parse(init.body);
        } catch (err) {
          console.error("Failed to parse chat payload", err);
        }
      }
      const messageList = rawBody.messages || [];
      const selectedSpace = rawBody.space ?? space;
      const lastUserMessage = [...messageList].reverse().find((m) => m.role === "user");
      const question = typeof lastUserMessage?.content === "string"
        ? lastUserMessage.content
        : Array.isArray(lastUserMessage?.content)
        ? lastUserMessage.content.map((p) => (typeof p === "string" ? p : p.text || "")).join("")
        : "";

      const authRaw = localStorage.getItem("auth");
      const token = authRaw ? JSON.parse(authRaw).token : null;
      const headers = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      lastAssistantMetaRef.current = { citations: [], file_url: null };

      const res = await fetch(`${API_BASE}/v1/chat/stream`, {
        method: "POST",
        headers,
        body: JSON.stringify({ question, space: selectedSpace }),
      });

      if (!res.ok || !res.body) {
        throw new Error(`Stream error ${res.status}`);
      }

      const reader = res.body.getReader();
      let buffer = "";
      let previousText = "";
      const finalMeta = { citations: [], file_url: null };

      const stream = new ReadableStream({
        async start(controller) {
          try {
            while (true) {
              const { value, done } = await reader.read();
              if (done) break;

              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split("\n");
              buffer = lines.pop() ?? "";

              for (const rawLine of lines) {
                const line = rawLine.trim();
                if (!line) continue;

                let evt;
                try {
                  evt = JSON.parse(line);
                } catch (err) {
                  console.error("Failed to parse stream event", err);
                  continue;
                }

                if (evt.type === "content") {
                  const text = evt.text ?? "";
                  const delta = text.slice(previousText.length);
                  previousText = text;
                  if (delta) controller.enqueue(encoder.encode(delta));
                } else if (evt.type === "done") {
                  finalMeta.citations = evt.citations || [];
                  finalMeta.file_url = evt.file_url || null;
                } else if (evt.type === "error") {
                  console.error("Stream error:", evt.message);
                }
              }
            }
          } catch (err) {
            controller.error(err);
            return;
          }

          lastAssistantMetaRef.current = finalMeta;
          controller.close();
        },
      });

      return new Response(stream, {
        headers: { "Content-Type": "text/plain; charset=utf-8" },
      });
    },
    onFinish: (message) => {
      const meta = lastAssistantMetaRef.current;
      setMessages((msgs) =>
        msgs.map((m) =>
          m.id === message.id
            ? {
                ...m,
                data: {
                  ...(m.data || {}),
                  citations: meta.citations,
                  file_url: meta.file_url,
                },
              }
            : m
        )
      );
    },
  });

  const renderedMessages = messages
    .filter((m) => m.role === "user" || m.role === "assistant")
    .map((m, idx, arr) => {
      const baseText = Array.isArray(m.content)
        ? m.content
            .map((part) =>
              typeof part === "string" ? part : part?.text ?? ""
            )
            .join("")
        : typeof m.content === "string"
        ? m.content
        : "";
      const isStreamingAssistant =
        m.role === "assistant" && idx === arr.length - 1 && isLoading;
      return {
        role: m.role === "assistant" ? "bot" : "user",
        text: baseText,
        citations: m.data?.citations || [],
        file_url: m.data?.file_url || null,
        streaming: isStreamingAssistant,
      };
    });

  const onSubmit = (event) => {
    if (!input.trim()) {
      event.preventDefault();
      return;
    }
    handleSubmit(event);
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
        {renderedMessages.map((m, idx) => (
          <ChatMessage key={idx} msg={m} baseUrl={API_BASE} />
        ))}
        {isLoading && <p className="text-slate-500">Generando…</p>}
      </div>

      {/* Input */}
      <form onSubmit={onSubmit} className="flex-shrink-0 flex space-x-2">
        <div className={`input-wrapper flex-grow relative ${input ? "caret-hidden" : ""}`}>
          <input
            type="text"
            className="flex-grow w-full py-3 px-4 border rounded-2xl
                                focus:outline-none focus:placeholder-transparent
                                hover:bg-gray-50 transition-colors"
            placeholder="Pregunta lo que quieras a tu asistente legal…"
            value={input}
            onChange={handleInputChange}
          />
        </div>
        <button
          type="submit"
          className="px-8 py-3 bg-gray-200 text-gray-900 border rounded-3xl hover:bg-gray-300 transition"
          disabled={isLoading}
        >
          Enviar
        </button>
      </form>
    </div>
  );
}
