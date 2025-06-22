// src/components/MarkdownText.jsx
import ReactMarkdown from "react-markdown";
import remarkGfm     from "remark-gfm";
import rehypeRaw     from "rehype-raw";

export default function MarkdownText({ text }) {
  return (
    <div className="prose lg:prose-xl prose-slate space-y-4">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
        components={{
          ol: (props) => <ol className="prose list-decimal pl-6 py-0 my-1" {...props} />,
          ul: (props) => <ul className="prose list-disc  pl-6 py-0 my-1" {...props} />,
          li: (props) => <li className="prose leading-relaxed py-0 my-1" {...props} />,
        }}
      >
        {text}
      </ReactMarkdown>
    </div>
  );
}
