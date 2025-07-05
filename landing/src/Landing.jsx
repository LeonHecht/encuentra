import { useForm, ValidationError } from '@formspree/react';
import Navbar from './components/Navbar';
import Countdown from './components/Countdown';

export default function Landing() {
  const [state, handleSubmit] = useForm("xpwrewon");

  /* ✅  Mensaje de éxito */
  if (state.succeeded) {
    return (
      <div className="min-h-screen flex flex-col relative z-10">
        <Navbar />
        <main className="flex-1 grid place-items-center px-4">
          <div className="
              max-w-md              /* móvil */
              md:max-w-xl                  /* ≥768 px */
              bg-green-200   /* ligerísima transparencia sobre vídeo */
              rounded-3xl shadow-xl
              p-8 sm:p-10 space-y-8"
          >
            <h1 className="text-2xl font-bold text-center">¡Gracias por unirte! 🎉</h1>
            <p className="text-gray-600 text-center">
              Te avisaremos en cuanto abra la beta.<br />
              Serás de los primeros en tener acceso prioritario.
            </p>
          </div>
        </main>
      </div>
    );
  }

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
            Encuentra — Unirme a la Lista de Espera
          </h1>

          <p className="text-center text-sm sm:text-base text-gray-600">
            Número de lugares: 50<br />
            Lanzamiento beta en&nbsp;<Countdown />
          </p>

          <form
            onSubmit={handleSubmit}
            className="space-y-4"
          >
            <input type="hidden" name="form-name" value="waitlist" />

            <input
              type="email"
              name="email"
              required
              placeholder="tu@email.com"
              className="w-full py-3 px-4 border rounded-2xl
                                focus:outline-none
                                hover:bg-gray-50 transition-colors
                                text-[16px]              /* evita zoom iOS */"
            />
            <ValidationError prefix="Email" field="email" errors={state.errors} />

            <input
              type="text"
              name="nombre"
              placeholder="Nombre (opcional)"
              className="w-full py-3 px-4 border rounded-2xl
                                focus:outline-none
                                hover:bg-gray-50 transition-colors"
            />
            <ValidationError prefix="Nombre" field="nombre" errors={state.errors} />
            
            <input
              type="text"
              name="institución"
              placeholder="Institución (opcional)"
              className="w-full py-3 px-4 border rounded-2xl
                                focus:outline-none
                                hover:bg-gray-50 transition-colors"
            />
            <ValidationError prefix="Institución" field="institución" errors={state.errors} />

            <button
              type="submit"
              disabled={state.submitting}
              className="w-full px-8 py-3 bg-gray-200 text-gray-900 rounded-3xl hover:bg-gray-300 transition"
            >
              {state.submitting ? 'Enviando…' : 'Unirme a la lista de espera'}
            </button>
          </form>

          <p className="text-xs text-gray-400 text-center">
            Inscripción sin ningún compromiso. No spam. © 2025 Encuentra
          </p>
        </div>
      </main>
    </div>
  );
}
