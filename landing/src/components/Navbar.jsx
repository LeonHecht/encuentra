import logo from '../assets/logo_full-removebg.png';

export default function Navbar() {
  return (
    <nav className="w-full bg-transparent">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-5 py-5 sm:px-8">
        <a href="#inicio" aria-label="Encuentra, inicio">
          <img
            src={logo}
            alt="Encuentra"
            className="h-8 w-auto"
          />
        </a>

        <div className="hidden items-center gap-8 text-[13px] font-semibold text-neutral-700 md:flex">
          <a className="transition-colors hover:text-black" href="#cobertura">
            Cobertura
          </a>
          <a className="transition-colors hover:text-black" href="#busqueda">
            Búsqueda
          </a>
          <a className="transition-colors hover:text-black" href="#analisis">
            Análisis
          </a>
        </div>

        <a
          href="https://staging.encuentra.app/login"
          className="inline-flex h-10 items-center justify-center rounded-full border border-black/15 bg-white/35 px-5 text-[13px] font-bold text-neutral-950 backdrop-blur-md transition hover:border-black/30 hover:bg-white/65"
        >
          Ingresar
        </a>
      </div>
    </nav>
  );
}
