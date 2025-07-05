// src/components/BackgroundVideo.jsx
export default function BackgroundVideo() {
  return (
    <video
      className="absolute inset-0 w-full h-full object-cover hidden md:block -z-10 opacity-50"
      autoPlay        // reproducción automática
      loop            // se repite
      muted           // sin sonido
      playsInline     // evita pantalla completa forzada en iOS
    >
      <source src="/assets/encuentra_landing(2).mp4" type="video/mp4" />
      {/* fallback para navegadores viejos */}
      Tu navegador no soporta vídeo en HTML5.
    </video>
  );
}
