// src/components/ChatMessage.jsx
import MarkdownText from "@/components/MarkdownText";
import useTypewriterMarkdown from "@/hooks/useTypewriterMarkdown";

export default function ChatMessage({ msg, baseUrl }) {
  // siempre llamamos al hook; si no es bot devolvemos el texto completo
  const content =
    msg.role === "bot" ? useTypewriterMarkdown(msg.text) : msg.text;

  return (
    <div
      className={`p-4 rounded-3xl ${
        msg.role === "user"
          ? "bg-gray-100 self-end"
          : "bg-white hover:bg-gray-50 border transition"
      }`}
    >
      {msg.role === "bot" ? (
        <MarkdownText text={content} />          
      ) : (
        <p className="whitespace-pre-wrap">{content}</p>  
      )}

      {msg.citations?.length > 0 && (
        <div className="mt-2 text-xs text-slate-500">
          Fuente: {msg.citations[0].doc_id}
        </div>
      )}

      {msg.file_url && (
        <a
          href={`${baseUrl}${msg.file_url}`}
          target="_blank"
          rel="noreferrer"
          className="text-indigo-600 underline mt-2 inline-block"
        >
          Descargar diagrama PNG
        </a>
      )}
    </div>
  );
}
