import { useState, useEffect } from "react";
import { useApi } from "@/hooks/useApi";
import { useChat } from "@ai-sdk/react";
import SpaceSelect from "@/components/SpaceSelect";
import ChatMessage from "@/components/ChatMessage";

export default function Chat() {
  const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
  const { messages, input, handleInputChange, handleSubmit, isLoading, error } = useChat({
    api: `${API_BASE}/v1/chat/stream`,   // your FastAPI endpoint
    headers: () => {
      const raw = localStorage.getItem("auth");
      const token = raw ? JSON.parse(raw).token : null;
      return token ? { Authorization: `Bearer ${token}` } : {};
    },
    body: { space }, // extra fields to send along with the messages
  });

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
        {messages.map((m, i) => (
          <ChatMessage key={i} msg={{ role: m.role, text: m.content }} baseUrl={API_BASE} />
        ))}
        {isLoading && <p className="text-slate-500">Generando…</p>}
        {error && <p className="text-red-600 text-sm">{String(error)}</p>}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex-shrink-0 flex space-x-2">
        <div className={`input-wrapper flex-grow relative ${question ? "caret-hidden" : ""}`}>
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
