import { useState } from "react";

export default function Chat() {
  const [messages, setMessages] = useState([]);

  return (
    <div className="h-screen flex flex-col p-6 bg-white">
      <h2 className="text-2xl font-semibold mb-4">Chat with your docs</h2>
      <div className="flex-1 overflow-auto mb-4 border rounded p-4">
        {messages.length === 0 ? (
          <p className="text-slate-500">No messages yet…</p>
        ) : (
          messages.map((m,i) => <div key={i}>{m}</div>)
        )}
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          // TODO: send to /v1/chat
        }}
        className="flex"
      >
        <input
          type="text"
          placeholder="Type your question…"
          className="flex-grow border p-2 rounded-l"
        />
        <button
          type="submit"
          className="bg-indigo-600 text-white px-4 rounded-r hover:bg-indigo-700"
        >
          Send
        </button>
      </form>
    </div>
  );
}
