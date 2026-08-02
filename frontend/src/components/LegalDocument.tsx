import { useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

export type LegalSection = {
  title: string;
  paragraphs?: ReactNode[];
  bullets?: ReactNode[];
};

export type LegalCopy = {
  title: string;
  summary: string;
  updatedLabel: string;
  sections: LegalSection[];
};

type LegalDocumentProps = {
  spanish: LegalCopy;
  english: LegalCopy;
};

export default function LegalDocument({ spanish, english }: LegalDocumentProps) {
  const [language, setLanguage] = useState<"es" | "en">(() => {
    if (typeof navigator === "undefined") return "es";
    return navigator.language.toLowerCase().startsWith("es") ? "es" : "en";
  });
  const copy = language === "es" ? spanish : english;

  return (
    <div className="h-full overflow-y-auto bg-[#F5F5F7] text-gray-900">
      <article className="mx-auto w-full max-w-4xl px-5 py-10 sm:px-8 sm:py-14">
        <div className="mb-10 flex flex-wrap items-start justify-between gap-5 border-b border-gray-200 pb-8">
          <div className="max-w-2xl">
            <Link
              to="/"
              className="mb-5 inline-flex text-sm font-medium text-gray-500 transition hover:text-gray-900"
            >
              ← Encuentra
            </Link>
            <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
              {copy.title}
            </h1>
            <p className="mt-4 text-base leading-7 text-gray-600">{copy.summary}</p>
            <p className="mt-3 text-sm text-gray-500">{copy.updatedLabel}</p>
          </div>

          <div
            className="inline-flex rounded-full border border-gray-300 bg-white p-1 text-sm"
            aria-label="Language / Idioma"
          >
            <button
              type="button"
              onClick={() => setLanguage("es")}
              className={`rounded-full px-4 py-2 transition ${
                language === "es" ? "bg-black text-white" : "text-gray-600 hover:text-black"
              }`}
              aria-pressed={language === "es"}
            >
              Español
            </button>
            <button
              type="button"
              onClick={() => setLanguage("en")}
              className={`rounded-full px-4 py-2 transition ${
                language === "en" ? "bg-black text-white" : "text-gray-600 hover:text-black"
              }`}
              aria-pressed={language === "en"}
            >
              English
            </button>
          </div>
        </div>

        <div className="space-y-10">
          {copy.sections.map((section, index) => (
            <section key={`${section.title}-${index}`}>
              <h2 className="text-xl font-semibold tracking-tight sm:text-2xl">
                {index + 1}. {section.title}
              </h2>
              {section.paragraphs?.map((paragraph, paragraphIndex) => (
                <p
                  key={paragraphIndex}
                  className="mt-4 text-[15px] leading-7 text-gray-700 sm:text-base"
                >
                  {paragraph}
                </p>
              ))}
              {section.bullets && (
                <ul className="mt-4 list-disc space-y-3 pl-6 text-[15px] leading-7 text-gray-700 sm:text-base">
                  {section.bullets.map((bullet, bulletIndex) => (
                    <li key={bulletIndex}>{bullet}</li>
                  ))}
                </ul>
              )}
            </section>
          ))}
        </div>

        <div className="mt-14 border-t border-gray-200 pt-7 text-sm text-gray-500">
          <Link to="/privacy" className="transition hover:text-gray-900">
            Privacidad / Privacy
          </Link>
          <span aria-hidden="true" className="mx-3">·</span>
          <Link to="/terms" className="transition hover:text-gray-900">
            Términos / Terms
          </Link>
          <span aria-hidden="true" className="mx-3">·</span>
          <a href="mailto:leon@encuentra.app" className="transition hover:text-gray-900">
            leon@encuentra.app
          </a>
        </div>
      </article>
    </div>
  );
}
