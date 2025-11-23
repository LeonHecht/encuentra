import { useForm, ValidationError } from '@formspree/react';
import Navbar from './components/Navbar';
import Countdown from './components/Countdown';
import ChatBox from './components/ChatBox';

export default function Landing() {
  return (
    <div className="relative z-10 flex flex-col min-h-screen">
      {/* top bar */}
      <Navbar />

      {/* hero / card */}
      <main className="flex-1 flex items-center justify-center px-4">
        <div className="
            w-full max-w-md              /* móvil */
            md:max-w-xl                  /* ≥768 px */
            bg-white/90 md:bg-white/70   /* ligerísima transparencia sobre vídeo */
            rounded-3xl shadow-xl
            p-8 sm:p-10 space-y-8
          ">

          <h1 className="text-2xl sm:text-3xl font-extrabold text-center">
            Encuentra – tu asistente legal con IA para El Salvador
          </h1>

          {/* Replaced waitlist form with ChatBox component */}
          <div className="space-y-4">
            <p className="text-center text-sm sm:text-base text-gray-600">
              Busca jurisprudencia, chatea con IA y sube documentos legales, todo en un solo lugar.
            </p>
            <ChatBox
              placeholder="Escribe tu mensaje..."
              onSend={(msg) => {
                // Simple redirect after sending; could include msg in querystring if desired.
                const targetUrl = 'https://example.com/gracias';
                window.location.href = targetUrl;
              }}
            />
          </div>

          <p className="text-xs text-gray-400 text-center">
            Únete a miles de abogados agilizando tu trabajo diario con IA. © 2025 Encuentra
          </p>
        </div>
      </main>
    </div>
  );
}
