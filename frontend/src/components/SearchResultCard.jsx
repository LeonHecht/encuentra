import { useEffect, useMemo, useState } from "react";
import {
  Calendar,
  ChevronDown,
  ChevronUp,
  Download,
  FileText,
  Scale,
  ThumbsDown,
  ThumbsUp,
} from "lucide-react";
import { apiFetch } from "@/hooks/useApi";

const API_BASE = (import.meta.env.VITE_API_BASE || "http://localhost:8000").replace(/\/+$/, "");

function renderEmAsStrong(snippet = "") {
  const parts = snippet.split(/(<em>.*?<\/em>)/g);
  return parts.map((part, idx) => {
    const m = part.match(/^<em>(.*?)<\/em>$/);
    if (m) return <b key={idx}>{m[1]}</b>;
    return <span key={idx}>{part}</span>;
  });
}

function asList(value) {
  if (!value) return [];
  if (Array.isArray(value)) return value.filter(Boolean);
  return [value].filter(Boolean);
}

function joinList(items, fallback = "Desconocido") {
  const list = asList(items);
  return list.length ? list.join(", ") : fallback;
}

function metadataText(value, fallback = "Desconocido") {
  return value || fallback;
}

function LoadingLine({ width = "w-48" }) {
  return (
    <span
      aria-label="Cargando informacion juridica"
      className={`inline-block h-3.5 ${width} animate-[pulse_1s_cubic-bezier(0.4,0,0.6,1)_infinite] rounded bg-gray-200 align-middle`}
    />
  );
}

function PendingText({ width }) {
  return <LoadingLine width={width} />;
}

function provisionLabel(item) {
  if (!item) return "";
  const pieces = [item.article, item.law].filter(Boolean);
  return pieces.length ? pieces.join(" ") : item.text_reference || "";
}

function InfoRow({ icon: Icon, label, children }) {
  return (
    <div className="grid grid-cols-[180px_1fr] gap-4 border-t border-gray-200 py-4">
      <div className="flex items-start gap-3 text-gray-800">
        <Icon className="mt-0.5 h-5 w-5 text-gray-500" aria-hidden="true" />
        <span className="text-sm font-semibold">{label}</span>
      </div>
      <div className="text-sm leading-6 text-gray-700">{children}</div>
    </div>
  );
}

export default function SearchResultCard({ result, space, feedback, onFeedback }) {
  const [metadataStatus, setMetadataStatus] = useState(result.metadata_status || "missing");
  const [metadata, setMetadata] = useState(result.metadata || null);
  const [expanded, setExpanded] = useState(false);
  const [pollingPaused, setPollingPaused] = useState(false);

  useEffect(() => {
    setMetadataStatus(result.metadata_status || "missing");
    setMetadata(result.metadata || null);
    setExpanded(false);
    setPollingPaused(false);
  }, [result.id, result.metadata_status, result.metadata]);

  useEffect(() => {
    if (metadataStatus !== "pending" || metadata || pollingPaused) return undefined;

    const maxPollingAttempts = 30;
    let attempts = 0;
    const intervalId = setInterval(async () => {
      attempts += 1;
      try {
        const response = await apiFetch(
          "case-metadata",
          `?space=${encodeURIComponent(space)}&doc_id=${encodeURIComponent(result.id)}`
        );
        setMetadataStatus(response.status || "missing");
        if (response.metadata) {
          setMetadata(response.metadata);
          clearInterval(intervalId);
        }
        if (response.status === "failed") {
          clearInterval(intervalId);
        }
        if (attempts >= maxPollingAttempts) {
          setPollingPaused(true);
          clearInterval(intervalId);
        }
      } catch {
        if (attempts >= maxPollingAttempts) {
          setPollingPaused(true);
          clearInterval(intervalId);
        }
      }
    }, 3000);

    return () => clearInterval(intervalId);
  }, [metadataStatus, metadata, pollingPaused, result.id, space]);

  const isMetadataPending = metadataStatus === "pending" && !metadata;
  const title = metadata?.generated_title || result.title || result.id;
  const court = metadata?.court_chamber;
  const typeTags = useMemo(
    () => [metadata?.resolution_type, ...(metadata?.legal_area_tags || []).slice(0, 2)].filter(Boolean),
    [metadata]
  );
  const parties = metadata?.parties || {};
  const authority = joinList(parties.defendants_or_authorities);
  const partySummary = joinList([
    ...asList(parties.actors),
    ...asList(parties.favored_parties),
    ...asList(parties.other_relevant_parties),
  ]);
  const provisions = (metadata?.key_legal_provisions || []).map(provisionLabel).filter(Boolean);
  const passage = result.snippet || "";
  const legalQuestions = asList(metadata?.legal_questions);

  return (
    <article className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm transition hover:shadow-md">
      <div className="flex items-start justify-between gap-6">
        <div className="min-w-0">
          <h3 className="text-lg font-semibold leading-6 text-gray-950">{title}</h3>
          <p className="mt-1 text-sm text-gray-600">
            {court || (isMetadataPending ? <PendingText width="w-64" /> : "Tribunal o sala desconocida")}
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {typeTags.length > 0 ? (
              typeTags.map((tag) => (
                <span key={tag} className="rounded-md border border-gray-200 bg-gray-50 px-2.5 py-1 text-xs text-gray-700">
                  {tag}
                </span>
              ))
            ) : (
              <span className="rounded-md border border-gray-200 bg-gray-50 px-2.5 py-1 text-xs text-gray-500">
                Información jurídica pendiente
              </span>
            )}
          </div>
        </div>
        <div className="shrink-0 text-right font-mono text-sm text-gray-500">
          {result.case_year && <div>Año: {result.case_year}</div>}
          <div>ID: {result.id}</div>
        </div>
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-[1fr_320px]">
        <div className="space-y-2 text-sm leading-6 text-gray-700">
          <p>
            <span className="font-semibold text-gray-900">Resultado:</span>{" "}
            {isMetadataPending ? <PendingText width="w-80" /> : metadataText(metadata?.outcome)}
          </p>
          <p>
            <span className="font-semibold text-gray-900">Partes:</span>{" "}
            {isMetadataPending ? <PendingText width="w-72" /> : partySummary}
          </p>
          <p>
            <span className="font-semibold text-gray-900">Autoridad:</span>{" "}
            {isMetadataPending ? <PendingText width="w-72" /> : authority}
          </p>
        </div>
        <div className="rounded-md border border-gray-200 bg-gray-50 p-3">
          <p className="text-sm font-semibold text-gray-900">Normas citadas</p>
          <p className="mt-2 text-sm leading-5 text-gray-700">
            {isMetadataPending ? <PendingText width="w-56" /> : provisions.length ? provisions.slice(0, 5).join("; ") : "Desconocido"}
          </p>
        </div>
      </div>

      <div className="mt-5">
        <p className="text-sm font-semibold text-gray-900">Fragmento relevante</p>
        <p className="mt-2 text-sm leading-6 text-gray-700">
          {renderEmAsStrong(passage)}
          {passage.split(" ").length >= 50 ? "..." : ""}
        </p>
        {metadataStatus === "pending" && !metadata && (
          <p className="mt-2 text-xs text-gray-500">Analizando información jurídica...</p>
        )}
      </div>

      <div className="relative mt-4 flex items-center gap-2">
        {result.download_url && (
          <a
            href={new URL(result.download_url, API_BASE).toString()}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 rounded-md bg-gray-200 px-4 py-2 text-sm text-gray-950 transition hover:bg-gray-100"
          >
            <Download className="h-4 w-4" aria-hidden="true" />
            Descargar PDF
          </a>
        )}
        <div className="ml-auto flex gap-2">
          <button
            onClick={() => onFeedback(result.id, true)}
            disabled={feedback != null}
            aria-label="Marcar resultado como útil"
            className={`rounded-full p-1.5 transition ${
              feedback === true ? "bg-green-200 text-green-800" : "text-gray-600 hover:bg-green-100"
            }`}
          >
            <ThumbsUp className="h-4 w-4" />
          </button>
          <button
            onClick={() => onFeedback(result.id, false)}
            disabled={feedback != null}
            aria-label="Marcar resultado como no útil"
            className={`rounded-full p-1.5 transition ${
              feedback === false ? "bg-red-200 text-red-800" : "text-gray-600 hover:bg-red-100"
            }`}
          >
            <ThumbsDown className="h-4 w-4" />
          </button>
        </div>
      </div>

      <button
        type="button"
        onClick={() => setExpanded((value) => !value)}
        aria-expanded={expanded}
        className="mt-5 flex w-full items-center justify-between rounded-md border border-gray-200 bg-gray-50 px-4 py-2.5 text-sm font-medium text-gray-800 transition hover:bg-gray-100"
      >
        {expanded ? "Ocultar información" : "Expandir información"}
        {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </button>

      {expanded && (
        <div>
          <InfoRow icon={FileText} label="Resumen jurídico">
            {metadataText(metadata?.legal_issue_summary)}
          </InfoRow>
          <InfoRow icon={Calendar} label="Fechas relevantes">
            {isMetadataPending ? (
              <div className="space-y-2">
                <PendingText width="w-64" />
                <PendingText width="w-52" />
              </div>
            ) : (metadata?.relevant_dates || []).length > 0 ? (
              <ul className="list-disc space-y-1 pl-5">
                {metadata.relevant_dates.map((item, index) => (
                  <li key={`${item.label}-${index}`}>
                    {item.date_text || "Desconocido"}: {item.label}
                  </li>
                ))}
              </ul>
            ) : (
              "Desconocido"
            )}
          </InfoRow>
          <InfoRow icon={Scale} label="Cuestiones jurídicas">
            {legalQuestions.length ? legalQuestions.join("; ") : "Desconocido"}
          </InfoRow>
        </div>
      )}
    </article>
  );
}
