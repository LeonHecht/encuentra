import { useEffect, useRef, useState } from 'react';

const PLACEHOLDER_QUESTIONS = [
  "¿Qué criterios hay sobre diligencia en contratos?",
  "Muéstrame precedentes de despido injustificado.",
  "¿Cómo interpretan los jueces la buena fe?",
  "Revisa esta cláusula de confidencialidad por riesgos.",
  "¿Qué reglas rigen la admisión de documentos?",
  "Identifica riesgos en este contrato de suministro.",
  "Búscame casos que apliquen el criterio X.",
  "¿Cómo se entiende el interés legítimo en amparo?",
  "Dame precedentes de responsabilidad médica por omisión.",
  "Resume la obligación de informar en consumo con citas."
];

/**
 * ChatBox component
 * Renders a dark rounded chat input bar similar to provided screenshot.
 * Props:
 *  - onSend(message: string): optional callback when message sent
 *  - placeholder: optional placeholder text
 */
export default function ChatBox({
  onSend,
  placeholder,
  disabled = false,
  animatePlaceholder = true,
}) {
  const [value, setValue] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);
  const textareaRef = useRef(null);

  // Rotate placeholders every 2 seconds
  useEffect(() => {
    if (!animatePlaceholder || placeholder) return undefined;

    const interval = setInterval(() => {
      setIsAnimating(true);
      setTimeout(() => {
        setCurrentIndex((prev) => (prev + 1) % PLACEHOLDER_QUESTIONS.length);
        setIsAnimating(false);
      }, 300); // Match animation duration
    }, 2000);

    return () => clearInterval(interval);
  }, [animatePlaceholder, placeholder]);

  // Auto resize height (optional nicer UX)
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
    el.style.overflowY = el.scrollHeight > 160 ? 'auto' : 'hidden';
  }, [value]);

  const handleSend = () => {
    if (disabled) return;
    const trimmed = value.trim();
    if (!trimmed) return;
    onSend?.(trimmed);
    setValue('');
  };

  const handleChange = (e) => {
    setValue(e.target.value);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className={`flex items-end gap-3 rounded-full bg-neutral-50 px-3 py-2 transition-colors hover:bg-neutral-100 focus-within:bg-neutral-100 ${disabled ? 'opacity-75' : ''}`}>
        <div className="relative flex min-h-8 flex-1 items-center overflow-hidden">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder={placeholder || ''}
            rows={1}
            disabled={disabled}
            className="relative px-1 z-10 max-h-40 w-full resize-none bg-transparent text-sm leading-relaxed text-neutral-800 caret-neutral-800 focus:outline-none"
            style={{
              color: value ? 'inherit' : 'transparent',
            }}
          />
          {!value && (
            <div className="px-1 pointer-events-none absolute inset-0 flex items-center overflow-hidden">
              <div
                className={`text-sm leading-relaxed text-neutral-400 transition-transform duration-500 ${animatePlaceholder && isAnimating
                  ? 'translate-y-full opacity-0'
                  : 'translate-y-0 opacity-100'
                  }`}
              >
                {placeholder || PLACEHOLDER_QUESTIONS[currentIndex]}
              </div>
            </div>
          )}
        </div>
        <button
          type="button"
          onClick={handleSend}
          aria-label="Send message"
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-neutral-900 text-white transition hover:bg-black disabled:opacity-40"
          disabled={disabled || !value.trim()}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="h-4 w-4"
          >
            <path d="M12 19V5" />
            <path d="M5 12l7-7 7 7" />
          </svg>
        </button>
      </div>
    </div>
  );
}
