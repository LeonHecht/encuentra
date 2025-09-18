import MarkdownText from "@/components/MarkdownText";

export default function ChatMessage({ msg, baseUrl }) {
  return (
    <div
      className={`p-4 rounded-3xl ${
        msg.role === "user"
          ? "bg-gray-100 self-end"
          : "bg-white hover:bg-gray-50 border transition"
      }`}
    >
      {msg.role === "bot" ? (
        <MarkdownText text={msg.text || ""} />
      ) : (
        <p className="whitespace-pre-wrap">{msg.text || ""}</p>
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
