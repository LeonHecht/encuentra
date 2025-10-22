import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";

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

type Cite = { doc_id: string; snippet?: string; title?: string; download_url?: string };

type Props = {
  text: string;
  citations?: Cite[];
  apiBase?: string;
  className?: string;
};

// Convert OpenSearch highlight tags <em>...</em> to React nodes with <strong>...
function renderEmAsStrong(snippet: string): React.ReactNode[] {
  const parts = snippet.split(/(<em>.*?<\/em>)/g);
  return parts.map((part, idx) => {
    const m = part.match(/^<em>(.*?)<\/em>$/);
    if (m) return <b key={idx}>{m[1]}</b>;
    return <span key={idx}>{part}</span>;
  });
}

// Replace any bracket group [ ... ] into a single <cite data-cites="<json>">[ ... ]</cite>
// Inside the brackets, support multiple citations separated by ';' or ','
// Each entry supports `DocID` or `DocID §hint`.
function embedCitationSpans(md: string): string {
  const pattern = /\[([^\]]+)\]/g;
  return md.replace(pattern, (match: string, inner: string) => {
    // Try to parse citations out of the bracket content.
    const parts = inner
      .split(/[;,]/)
      .map((s) => s.trim())
      .filter(Boolean);

    const cites = parts
      .map((p) => {
        const segs = p.split(/§/);
        const doc = (segs[0] || "").trim();
        const hint = (segs[1] || "").trim();
        if (!doc) return null;
        // Only accept plain doc ids (no spaces)
        if (/\s/.test(doc)) return null;
        return { doc, hint };
      })
      .filter(Boolean) as Array<{ doc: string; hint: string }>;

    if (cites.length === 0) return match; // not a citation group, leave unchanged

    const payload = encodeURIComponent(JSON.stringify(cites));
    // Preserve original visible text inside the cite
    return `<cite data-cites="${payload}">${match}</cite>`;
  });
}

// Normalize adjacent bracketed citations like "[40793] [100399]" into a single group
// "[40793; 100399]" so they render as one carousel.
function mergeAdjacentBracketCitations(md: string): string {
  let prev: string;
  let cur = md;
  const rx = /\[([^\]]+)\](\s*)\[([^\]]+)\]/g;
  // Repeat until no more merges can be made (handles 3+ in a row)
  do {
    prev = cur;
    cur = cur.replace(rx, (_m, a, ws, b) => `[${a}; ${b}]`);
  } while (cur !== prev);
  return cur;
}

export default function MarkdownWithCitations({ text, citations = [], apiBase, className }: Props) {
  // Preprocess markdown to include <cite ...> markers that we map to InlineCitation components
  const withCites = React.useMemo(() => embedCitationSpans(mergeAdjacentBracketCitations(text || "")), [text]);

  const CiteRenderer = ({ node, children }: any) => {
    const props = (node && (node.properties as any)) || {};
    const dataCites: string | undefined = props["dataCites"] || props["data-cites"];

    let items: Array<{ doc: string; hint: string }> = [];
    try {
      if (typeof dataCites === "string" && dataCites.length) {
        items = JSON.parse(decodeURIComponent(dataCites));
      }
    } catch {}

    // Map items to full citation objects using the provided citations prop
    // Goal: get the citation snippets that were provided by backend
    const merged = items.map(({ doc, hint }) => {
      const cit = citations.find((c) => c.doc_id === doc);
      const title = cit?.title || `Documento ${doc}`;
      const url = cit?.download_url || (apiBase ? `${apiBase}/files/${doc}.pdf` : undefined);
      const snippet = cit?.snippet;
      return { doc, hint, title, url, snippet };
    });

  const triggerSources = merged.map((m) => m.url).filter(Boolean) as string[];
  const triggerIds = merged.map((m) => m.doc);

    return (
      <InlineCitation>
        {/* <InlineCitationText>{children}</InlineCitationText> */}
        <InlineCitationCard>
          <InlineCitationCardTrigger sources={triggerSources} ids={triggerIds} />
          <InlineCitationCardBody>
            <InlineCitationCarousel>
              <InlineCitationCarouselHeader>
                <InlineCitationCarouselPrev />
                <InlineCitationCarouselIndex />
                <InlineCitationCarouselNext />
              </InlineCitationCarouselHeader>
              <InlineCitationCarouselContent>
                {merged.map((m, idx) => (
                  <InlineCitationCarouselItem key={`cite-item-${idx}`}>
                    <InlineCitationSource title={m.title}>
                      {m.snippet && (
                        <InlineCitationQuote>
                          {renderEmAsStrong(m.snippet)}
                        </InlineCitationQuote>
                      )}
                      {!m.snippet && m.hint && (
                        <InlineCitationQuote>{m.hint}</InlineCitationQuote>
                      )}
                    </InlineCitationSource>
                  </InlineCitationCarouselItem>
                ))}
              </InlineCitationCarouselContent>
            </InlineCitationCarousel>
          </InlineCitationCardBody>
        </InlineCitationCard>
      </InlineCitation>
    );
  };

  return (
    <div className={className}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
        // Allow rendering <cite> as our InlineCitation UI
        components={{ cite: CiteRenderer }}
      >
        {withCites}
      </ReactMarkdown>
    </div>
  );
}
