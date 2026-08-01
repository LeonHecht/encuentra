import { useEffect, useState } from 'react';
import { ArrowUp } from 'lucide-react';

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
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="flex items-center gap-3 rounded-full bg-white px-3 py-1.5 transition-colors">
        <div className="relative flex min-h-10 flex-1 items-center sm:min-h-8">
          <input
            type="text"
            value={value}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder=""
            aria-label={placeholder || PLACEHOLDER_QUESTIONS[currentIndex]}
            disabled={disabled}
            className="relative z-10 block h-10 min-w-0 w-full truncate bg-transparent px-1 text-sm leading-5 text-neutral-800 caret-neutral-800 focus:outline-none sm:h-8"
            style={{
              color: value ? 'inherit' : 'transparent',
            }}
          />
          {!value && (
            <div
              aria-hidden="true"
              className="pointer-events-none absolute inset-0 flex items-center overflow-hidden px-1"
            >
              <div
                className={`min-w-0 max-w-full truncate whitespace-nowrap text-sm leading-5 text-neutral-400 transition-transform duration-500 ${animatePlaceholder && isAnimating
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
          <ArrowUp aria-hidden="true" className="h-4 w-4" strokeWidth={2} />
        </button>
      </div>
    </div>
  );
}
