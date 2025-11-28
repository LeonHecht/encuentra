import Navbar from './components/Navbar';
import ChatBox from './components/ChatBox';

export default function Landing() {
  return (
    <div className="relative z-10 flex flex-col min-h-screen">
      {/* top bar */}
      <Navbar />

      {/* hero / card */}
      <main className="flex-1 flex flex-col px-4">
        {/* Hero section fills remaining viewport height */}
        <section className="flex-1 flex flex-col items-center justify-center">
          <div className="flex flex-col gap-5 max-w-2xl w-full">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-center">
              Encuentra – tu asistente legal con IA para El Salvador
            </h1>

            {/* Replaced waitlist form with ChatBox component */}
            <div className="space-y-20">
              <p className="text-center text-sm sm:text-base text-gray-600">
                Busca jurisprudencia, chatea con IA y sube documentos legales, todo en un solo lugar.
              </p>
              <ChatBox
                onSend={(msg) => {
                  // Simple redirect after sending; could include msg in querystring if desired.
                  const targetUrl = 'https://example.com/gracias';
                  window.location.href = targetUrl;
                }}
              />
            </div>
          </div>
        </section>

        {/* Future sections: feedback, features, etc. */}
        <section className="py-16 space-y-10">
          <div className="max-w-3xl mx-auto text-center text-gray-600 text-sm sm:text-base">
            <p>Sección para testimonios, casos de uso y características del producto.</p>
          </div>
        </section>
      </main>
    </div>
  );
}
