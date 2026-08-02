import {
  ArrowLeft,
  ArrowRight,
  Check,
  ChevronDown,
  FileText,
  Search as SearchIcon,
  ShieldCheck,
  ThumbsDown,
  ThumbsUp,
  X,
} from 'lucide-react';
import Navbar from './components/Navbar';
import BackgroundVideo from './components/BackgroundVideo';
import ChatBox from './components/ChatBox';
import { HeroParallax, ScrollReveal } from './components/ScrollMotion';
import StaticSearchResultCard from './components/StaticSearchResultCard';

const sampleResults = [
  {
    id: 'SL-CIV-142-2024',
    title: 'Sentencia 142-2024, Sala de lo Civil',
    case_year: 2024,
    snippet:
      'La Sala reitero que la <em>buena fe contractual</em> exige conducta coherente durante la negociacion, ejecucion y terminacion del contrato, especialmente cuando una parte ha generado confianza razonable en la otra.',
    metadata: {
      generated_title:
        'Buena fe contractual y confianza legítima en contratos mercantiles',
      court_chamber: 'Sala de lo Civil de la Corte Suprema de Justicia',
      resolution_type: 'Sentencia definitiva',
      legal_area_tags: ['Contratos mercantiles', 'Responsabilidad civil'],
      outcome: 'Se confirma parcialmente la responsabilidad por incumplimiento.',
      parties: {
        actors: ['Distribuidora Centroamericana, S.A. de C.V.'],
        defendants_or_authorities: ['Sociedad proveedora demandada'],
      },
      key_legal_provisions: [
        { article: 'Art. 1416', law: 'Código Civil' },
        { article: 'Art. 999', law: 'Código de Comercio' },
      ],
      legal_issue_summary:
        'El tribunal analiza si la conducta previa de las partes creó expectativas protegibles bajo el principio de buena fe.',
      relevant_dates: [
        { date_text: '12 de marzo de 2024', label: 'sentencia definitiva' },
      ],
      legal_questions: [
        'Alcance de la buena fe en la ejecución contractual',
        'Efectos de la confianza legítima entre comerciantes',
      ],
    },
  },
  {
    id: 'AMP-67-2023',
    title: 'Amparo 67-2023, Sala de lo Constitucional',
    case_year: 2023,
    snippet:
      'El tribunal valoro la carga argumentativa necesaria para acreditar una afectacion concreta al <em>derecho de defensa</em> y al debido proceso.',
    metadata: {
      generated_title: 'Debido proceso y derecho de defensa en sede administrativa',
      court_chamber: 'Sala de lo Constitucional',
      resolution_type: 'Amparo',
      legal_area_tags: ['Debido proceso', 'Derecho administrativo'],
      outcome: 'Se declara ha lugar el amparo solicitado.',
      parties: {
        actors: ['Particular afectado'],
        defendants_or_authorities: ['Autoridad administrativa sancionadora'],
      },
      key_legal_provisions: [
        { article: 'Art. 11', law: 'Constitución' },
        { article: 'Art. 12', law: 'Constitución' },
      ],
      legal_issue_summary:
        'La resolución estudia los mínimos de motivación y audiencia previa antes de imponer sanciones administrativas.',
      relevant_dates: [
        { date_text: '8 de septiembre de 2023', label: 'resolución de amparo' },
      ],
      legal_questions: ['Motivación suficiente', 'Oportunidad real de defensa'],
    },
  },
];

const chatMessages = [
  {
    id: 'sample-user',
    role: 'user',
    text: 'Resume el criterio sobre buena fe contractual y dime qué casos puedo citar.',
  },
  {
    id: 'sample-assistant',
    role: 'assistant',
    text:
      'El criterio central es que la buena fe opera como estándar de conducta durante toda la relación contractual. En los resultados seleccionados, la Sala vincula ese estándar con confianza legítima, coherencia de conducta y deber de colaboración.',
  },
];

function SearchRoutePreview() {
  return (
    <div className="w-full flex-1 overflow-hidden rounded-2xl border border-gray-200 bg-[#F5F5F7] px-4 py-6 shadow-xl shadow-gray-200/70 sm:px-6 lg:px-8">
      <div className="mx-auto w-full max-w-6xl space-y-4">
        <h2 className="text-2xl font-semibold">Buscar casos</h2>

        <div className="mb-6 grid gap-3 rounded-lg border border-gray-200 bg-white p-3 shadow-sm sm:p-4 lg:flex lg:items-end lg:gap-4">
          <div className="min-w-0 lg:w-72 lg:shrink-0">
            <div className="flex h-11 w-full items-center rounded-xl border border-gray-200 bg-white px-3 text-sm text-gray-900 shadow-sm">
              Todo El Salvador
            </div>
          </div>
          <div className="flex h-11 min-w-0 items-center rounded-xl border border-gray-200 bg-background px-4 text-base text-gray-900 shadow-sm md:text-sm lg:flex-1">
            buena fe contractual incumplimiento
          </div>
          <div className="grid grid-cols-2 gap-3 lg:contents">
            <label className="flex items-center gap-2 text-sm text-gray-600 lg:w-32 lg:shrink-0">
              <span className="shrink-0">Año</span>
              <div className="flex h-11 min-w-0 flex-1 items-center rounded-xl border border-gray-200 bg-background px-3 text-sm text-gray-500 shadow-sm">
                Todos
              </div>
            </label>
            <label className="flex items-center gap-2 text-sm text-gray-600 lg:w-40 lg:shrink-0">
              <span className="shrink-0">Mostrar</span>
              <div className="flex h-11 min-w-0 flex-1 items-center rounded-xl border border-gray-200 bg-white px-3 text-sm text-gray-900 shadow-sm">
                10
              </div>
            </label>
          </div>
          <div className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-xl bg-gray-200 px-6 text-sm font-medium text-gray-950 shadow-sm sm:w-auto lg:min-w-32">
            <SearchIcon className="h-4 w-4" aria-hidden="true" />
            Buscar
          </div>
        </div>

        <div className="space-y-4">
          {sampleResults.map((result, index) => (
            <StaticSearchResultCard
              key={result.id}
              result={result}
              feedback={index === 0 ? true : undefined}
              isInChatContext={index === 0}
              expanded={index === 0}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function ChatRoutePreview() {
  return (
    <div className="overflow-hidden rounded-2xl border border-gray-200 bg-[#F5F5F7] shadow-xl shadow-gray-200/70">
      <div className="flex min-h-[640px] flex-col overflow-hidden">
        <div className="flex items-center gap-4 p-4">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-gray-200 bg-white text-gray-700 shadow-sm">
            <span className="h-4 w-4 rounded border-y-2 border-gray-500" />
          </div>
          <div className="ml-1 flex h-11 w-80 max-w-[55%] items-center rounded-xl border border-gray-200 bg-white px-3 text-sm text-gray-900 shadow-sm">
            Todo El Salvador
          </div>
          <div className="ml-auto inline-flex h-10 shrink-0 items-center gap-2 rounded-xl border border-gray-200 bg-white px-4 text-sm font-medium text-gray-900 shadow-sm">
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            Volver a búsqueda
          </div>
        </div>

        <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
          <div className="min-h-0 flex-1 overflow-hidden px-3 pt-2 pb-24">
            <div className="mx-auto w-full max-w-4xl">
              <div className="space-y-4">
                {chatMessages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex w-full ${message.role === 'user' ? 'justify-end' : 'justify-start'
                      }`}
                  >
                    <div
                      className={`max-w-[85%] rounded-3xl p-4 text-sm leading-6 shadow-sm ${message.role === 'user'
                        ? 'bg-gray-100 text-gray-950'
                        : 'border bg-white text-gray-800'
                        }`}
                    >
                      <p className="whitespace-pre-wrap">{message.text}</p>
                      {message.role === 'assistant' && (
                        <>
                          <div className="mt-3 rounded-xl border border-gray-200 bg-gray-50 p-3">
                            <p className="text-xs font-medium uppercase text-gray-500">
                              Fuentes
                            </p>
                            <div className="mt-2 flex flex-wrap gap-2">
                              <span className="inline-flex items-center gap-2 rounded-md border border-gray-200 bg-white px-2.5 py-1.5 text-sm text-gray-800">
                                <FileText className="h-4 w-4 text-gray-500" />
                                SL-CIV-142-2024
                              </span>
                              <span className="inline-flex items-center gap-2 rounded-md border border-gray-200 bg-white px-2.5 py-1.5 text-sm text-gray-800">
                                <FileText className="h-4 w-4 text-gray-500" />
                                AMP-67-2023
                              </span>
                            </div>
                          </div>
                          <div className="mt-3 flex items-center gap-2 text-gray-600">
                            <span className="rounded-full bg-green-200 p-1.5 text-green-800">
                              <ThumbsUp className="h-4 w-4" />
                            </span>
                            <span className="rounded-full p-1.5">
                              <ThumbsDown className="h-4 w-4" />
                            </span>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="mx-auto w-full max-w-3xl shrink-0 px-3 pb-3">
            <div className="mb-2 rounded-lg border border-gray-200 bg-white px-3 py-2 shadow-sm">
              <div className="mb-2 flex items-center justify-between gap-3">
                <div className="text-xs font-medium uppercase text-gray-500">
                  Contexto del chat
                </div>
                <span className="text-xs text-gray-500">Quitar todos</span>
              </div>
              <div className="flex flex-wrap gap-2">
                <span className="inline-flex max-w-full items-center gap-2 rounded-md border border-gray-200 bg-gray-50 px-2.5 py-1.5 text-sm text-gray-800">
                  <FileText className="h-4 w-4 shrink-0 text-gray-500" aria-hidden="true" />
                  <span className="min-w-0 truncate">
                    Buena fe contractual y confianza legítima · 2024
                  </span>
                  <span className="rounded p-0.5 text-gray-500">
                    <X className="h-3.5 w-3.5" aria-hidden="true" />
                  </span>
                </span>
              </div>
            </div>
            <ChatBox
              onSend={() => { }}
              disabled
              animatePlaceholder={false}
              placeholder="Pregunta lo que quieras"
            />
            <p className="mt-2 text-center text-xs text-gray-500">
              Encuentra Chat puede cometer errores. Se debe comprobar la información importante.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Landing() {
  return (
    <div className="min-h-[100svh] overflow-x-clip bg-[#f4f4f4] text-gray-950">
      <div id="inicio" className="relative isolate min-h-[100svh] overflow-hidden">
        <BackgroundVideo />
        <div className="relative z-10">
          <Navbar />

          <section className="relative flex min-h-[calc(100svh-72px)] flex-col items-center justify-center px-4 pb-28 pt-16">
            <HeroParallax className="flex w-full max-w-3xl flex-col gap-8">
              <div className="space-y-2 text-center">
                <h1 className="text-6xl font-bold tracking-tight md:text-6xl">
                  encuentra
                </h1>
                <p className="mx-auto max-w-2xl text-base text-gray-600 sm:text-lg">
                  Busca precedentes, conversa con IA y trabaja con documentos legales de El Salvador desde un mismo espacio.
                </p>
              </div>

              <ChatBox
                onSend={(msg) => {
                  const targetUrl = 'https://staging.encuentra.app/login';
                  window.location.href = `${targetUrl}?q=${encodeURIComponent(msg)}`;
                }}
              />
            </HeroParallax>

            <a
              href="#cobertura"
              className="group absolute bottom-5 left-1/2 flex -translate-x-1/2 flex-col items-center gap-2 pb-[env(safe-area-inset-bottom)] text-[10px] font-bold uppercase tracking-[0.22em] text-neutral-700 transition-colors hover:text-black"
            >
              Conoce más
              <ChevronDown className="h-5 w-5 transition-transform motion-safe:animate-bounce group-hover:translate-y-1" />
            </a>
          </section>
        </div>
      </div>

      <main className="relative z-10 flex flex-col">
        <section id="cobertura" className="scroll-mt-20 bg-[#f4f4f4] px-4">
          <div className="mx-auto w-full max-w-7xl py-20">
            <div className="grid gap-8 py-14 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
              <ScrollReveal direction="left">
                <h2 className="mt-4 text-3xl font-bold tracking-tight text-gray-950 sm:text-5xl">
                  Más de 190,000 documentos legales para buscar, analizar y consultar en chat
                </h2>
              </ScrollReveal>
              <ScrollReveal
                direction="right"
                delay={140}
                className="space-y-5 text-base leading-7 text-gray-600 sm:text-lg"
              >
                <p>
                  Encuentra indexa documentos de cámaras, tribunales, salas y juzgados para que puedas buscar por tema, palabras clave, institución, año o criterio jurídico.
                </p>
                <p>
                  De cada documento se extrae información útil para investigar más rápido: tribunal, tipo de resolución, partes, resultado, normas citadas, preguntas jurídicas, fechas relevantes y fragmentos donde aparece el criterio.
                </p>
              </ScrollReveal>
            </div>
          </div>
        </section>

        <section id="busqueda" className="scroll-mt-20 bg-[#e9e9e9] px-4">
          <div className="mx-auto w-full max-w-7xl py-20">
            <div className="space-y-8">
              <ScrollReveal className="max-w-3xl">
                <h2 className="mt-3 text-3xl font-bold tracking-tight text-gray-950 sm:text-4xl">
                  Encuentra el criterio jurídico, no solo la palabra exacta
                </h2>
                <p className="mt-4 text-base leading-7 text-gray-600">
                  La búsqueda combina coincidencias textuales con señales extraídas del documento para mostrar resultados con contexto: resumen del caso, autoridades, normas citadas, área legal y el fragmento relevante para decidir rápidamente qué abrir o llevar al chat.
                </p>
              </ScrollReveal>
              <ScrollReveal direction="scale" delay={100}>
                <SearchRoutePreview />
              </ScrollReveal>
            </div>
          </div>
        </section>

        <section id="analisis" className="scroll-mt-20 bg-[#dedede] px-4">
          <div className="mx-auto w-full max-w-7xl py-20">
            <div className="space-y-8">
              <ScrollReveal className="max-w-3xl">
                <h2 className="mt-3 text-3xl font-bold tracking-tight text-gray-950 sm:text-4xl">
                  Pregunta, compara y resume usando documentos concretos
                </h2>
                <p className="mt-4 text-base leading-7 text-gray-600">
                  Puedes enviar resultados al chat para pedir resúmenes, comparar criterios entre resoluciones, preparar argumentos, ubicar citas y hacer preguntas de seguimiento sin perder las fuentes que ya encontraste.
                </p>
              </ScrollReveal>
              <ScrollReveal direction="scale" delay={100}>
                <ChatRoutePreview />
              </ScrollReveal>
            </div>
          </div>
        </section>

        <section id="privacidad" className="flex min-h-[70svh] scroll-mt-20 items-center bg-[#d3d3d3] px-4">
          <div className="mx-auto w-full max-w-7xl py-16 sm:py-20">
            <ScrollReveal className="w-full">
              <div className="grid gap-8 lg:grid-cols-[0.72fr_1.28fr] lg:gap-16">
                <div className="flex items-start gap-4">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-black/15 bg-white/40">
                    <ShieldCheck className="h-5 w-5 text-gray-800" aria-hidden="true" />
                  </div>
                  <p className="pt-3 text-xs font-bold uppercase tracking-[0.2em] text-gray-600">
                    Privacidad por diseño
                  </p>
                </div>

                <div className="max-w-3xl">
                  <h2 className="text-3xl font-bold tracking-tight text-gray-950 sm:text-5xl">
                    Privacidad basada en estándares europeos
                  </h2>
                  <p className="mt-6 text-base leading-7 text-gray-600 sm:text-lg">
                    Diseñado conforme a los principios del RGPD: no vendemos tus datos y no utilizamos tus documentos ni conversaciones para entrenar modelos.
                  </p>
                  <a
                    href="https://staging.encuentra.app/privacy"
                    className="group mt-8 inline-flex items-center gap-2 text-sm font-semibold text-gray-950"
                  >
                    Conoce cómo protegemos tus datos
                    <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" aria-hidden="true" />
                  </a>
                </div>
              </div>
            </ScrollReveal>
          </div>
        </section>

        <section className="min-h-[70svh] bg-[#484848] px-5 text-white sm:px-8">
          <div className="mx-auto flex min-h-[70svh] w-full max-w-7xl flex-col pb-8">
            <div className="flex flex-1 items-center py-16 sm:py-20">
              <ScrollReveal className="w-full">
                <div className="grid gap-10 lg:grid-cols-[1fr_auto] lg:items-center">
                  <div>
                    <h2 className="max-w-4xl text-4xl font-semibold leading-[1.04] tracking-[-0.045em] sm:text-6xl">
                      La investigación rigurosa también puede ser más ágil.
                    </h2>
                  </div>

                  <a
                    href="https://staging.encuentra.app/login"
                    className="group inline-flex h-14 items-center justify-center gap-3 rounded-full bg-white px-7 text-sm font-bold text-neutral-950 transition hover:bg-neutral-200"
                  >
                    Entrar a Encuentra
                    <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                  </a>
                </div>
              </ScrollReveal>
            </div>

            <footer className="flex flex-col gap-3 border-t border-white/10 pt-7 text-xs text-neutral-400 sm:flex-row sm:items-center sm:justify-between">
              <span>© 2026 Encuentra</span>
              <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
                <a
                  href="https://staging.encuentra.app/privacy"
                  className="transition hover:text-white"
                >
                  Privacidad
                </a>
                <a
                  href="https://staging.encuentra.app/terms"
                  className="transition hover:text-white"
                >
                  Términos
                </a>
                <span>Tecnología para la práctica jurídica en El Salvador.</span>
              </div>
            </footer>
          </div>
        </section>
      </main>
    </div>
  );
}
