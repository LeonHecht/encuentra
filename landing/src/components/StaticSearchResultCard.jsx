import { createElement } from 'react';
import {
  Calendar,
  Check,
  ChevronDown,
  ExternalLink,
  FileText,
  MessageSquare,
  Scale,
  ThumbsDown,
  ThumbsUp,
} from 'lucide-react';

function renderEmAsStrong(snippet = '') {
  const parts = snippet.split(/(<em>.*?<\/em>)/g);
  return parts.map((part, idx) => {
    const match = part.match(/^<em>(.*?)<\/em>$/);
    if (match) return <b key={idx}>{match[1]}</b>;
    return <span key={idx}>{part}</span>;
  });
}

function asList(value) {
  if (!value) return [];
  if (Array.isArray(value)) return value.filter(Boolean);
  return [value].filter(Boolean);
}

function joinList(items, fallback = 'Desconocido') {
  const list = asList(items);
  return list.length ? list.join(', ') : fallback;
}

function metadataText(value, fallback = 'Desconocido') {
  return value || fallback;
}

function provisionLabel(item) {
  if (!item) return '';
  const pieces = [item.article, item.law].filter(Boolean);
  return pieces.length ? pieces.join(' ') : item.text_reference || '';
}

function InfoRow({ icon, label, children }) {
  return (
    <div className="grid gap-3 border-t border-gray-200 py-4 sm:grid-cols-[180px_1fr] sm:gap-4">
      <div className="flex items-start gap-3 text-gray-800">
        {createElement(icon, {
          className: 'mt-0.5 h-5 w-5 text-gray-500',
          'aria-hidden': true,
        })}
        <span className="text-sm font-semibold">{label}</span>
      </div>
      <div className="text-sm leading-6 text-gray-700">{children}</div>
    </div>
  );
}

export default function StaticSearchResultCard({
  result,
  feedback,
  isInChatContext = false,
  expanded = false,
}) {
  const metadata = result.metadata || null;
  const title = metadata?.generated_title || result.title || result.id;
  const court = metadata?.court_chamber;
  const typeTags = [
    metadata?.resolution_type,
    ...(metadata?.legal_area_tags || []).slice(0, 2),
  ].filter(Boolean);
  const parties = metadata?.parties || {};
  const authority = joinList(parties.defendants_or_authorities);
  const partySummary = joinList([
    ...asList(parties.actors),
    ...asList(parties.favored_parties),
    ...asList(parties.other_relevant_parties),
  ]);
  const provisions = (metadata?.key_legal_provisions || [])
    .map(provisionLabel)
    .filter(Boolean);
  const passage = result.snippet || '';
  const legalQuestions = asList(metadata?.legal_questions);

  return (
    <article className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition hover:shadow-md sm:p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between sm:gap-6">
        <div className="min-w-0">
          <h3 className="text-lg font-semibold leading-6 text-gray-950">{title}</h3>
          <p className="mt-1 text-sm text-gray-600">
            {court || 'Tribunal o sala desconocida'}
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {typeTags.length > 0 ? (
              typeTags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-md border border-gray-200 bg-gray-50 px-2.5 py-1 text-xs text-gray-700"
                >
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
        <div className="max-w-full break-all font-mono text-xs text-gray-500 sm:shrink-0 sm:text-right sm:text-sm">
          {result.case_year && <div>Año: {result.case_year}</div>}
          <div>ID: {result.id}</div>
        </div>
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_320px]">
        <div className="space-y-2 text-sm leading-6 text-gray-700">
          <p>
            <span className="font-semibold text-gray-900">Resultado:</span>{' '}
            {metadataText(metadata?.outcome)}
          </p>
          <p>
            <span className="font-semibold text-gray-900">Partes:</span>{' '}
            {partySummary}
          </p>
          <p>
            <span className="font-semibold text-gray-900">Autoridad:</span>{' '}
            {authority}
          </p>
        </div>
        <div className="rounded-md border border-gray-200 bg-gray-50 p-3">
          <p className="text-sm font-semibold text-gray-900">Normas citadas</p>
          <p className="mt-2 text-sm leading-5 text-gray-700">
            {provisions.length ? provisions.slice(0, 5).join('; ') : 'Desconocido'}
          </p>
        </div>
      </div>

      <div className="mt-5">
        <p className="text-sm font-semibold text-gray-900">Fragmento relevante</p>
        <p className="mt-2 text-sm leading-6 text-gray-700">
          {renderEmAsStrong(passage)}
          {passage.split(' ').length >= 50 ? '...' : ''}
        </p>
      </div>

      <div className="relative mt-4 flex flex-wrap items-center gap-2">
        <span className="inline-flex min-h-10 items-center gap-2 rounded-md bg-gray-200 px-4 py-2 text-sm text-gray-950">
          <ExternalLink className="h-4 w-4" aria-hidden="true" />
          Abrir PDF
        </span>
        <span
          className={`inline-flex min-h-10 items-center gap-2 rounded-md px-4 py-2 text-sm ${
            isInChatContext
              ? 'border border-gray-300 bg-white text-gray-900'
              : 'bg-gray-950 text-white'
          }`}
        >
          {isInChatContext ? (
            <Check className="h-4 w-4" aria-hidden="true" />
          ) : (
            <MessageSquare className="h-4 w-4" aria-hidden="true" />
          )}
          {isInChatContext ? 'Añadido' : 'Usar en chat'}
        </span>
        {isInChatContext && (
          <span className="inline-flex min-h-10 items-center rounded-md border border-gray-200 bg-white px-4 py-2 text-sm text-gray-900">
            Ir al chat
          </span>
        )}
        <div className="ml-auto flex gap-2">
          <span
            aria-label="Marcar resultado como útil"
            className={`rounded-full p-1.5 transition ${
              feedback === true ? 'bg-green-200 text-green-800' : 'text-gray-600'
            }`}
          >
            <ThumbsUp className="h-4 w-4" />
          </span>
          <span
            aria-label="Marcar resultado como no útil"
            className={`rounded-full p-1.5 transition ${
              feedback === false ? 'bg-red-200 text-red-800' : 'text-gray-600'
            }`}
          >
            <ThumbsDown className="h-4 w-4" />
          </span>
        </div>
      </div>

      <div className="mt-5 flex w-full items-center justify-between gap-3 rounded-md border border-gray-200 bg-gray-50 px-4 py-2.5 text-left text-sm font-medium text-gray-800">
        {expanded ? 'Ocultar información' : 'Expandir información'}
        <ChevronDown className="h-4 w-4" />
      </div>

      {expanded && (
        <div>
          <InfoRow icon={FileText} label="Resumen jurídico">
            {metadataText(metadata?.legal_issue_summary)}
          </InfoRow>
          <InfoRow icon={Calendar} label="Fechas relevantes">
            {(metadata?.relevant_dates || []).length > 0 ? (
              <ul className="list-disc space-y-1 pl-5">
                {metadata.relevant_dates.map((item, index) => (
                  <li key={`${item.label}-${index}`}>
                    {item.date_text || 'Desconocido'}: {item.label}
                  </li>
                ))}
              </ul>
            ) : (
              'Desconocido'
            )}
          </InfoRow>
          <InfoRow icon={Scale} label="Cuestiones jurídicas">
            {legalQuestions.length ? legalQuestions.join('; ') : 'Desconocido'}
          </InfoRow>
        </div>
      )}
    </article>
  );
}
