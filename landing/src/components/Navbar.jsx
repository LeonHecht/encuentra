import logo from '../assets/logo_full-removebg.png';

export default function Navbar() {
  return (
    <nav className="w-full bg-white shadow-sm">
      <div className="w-full flex items-center px-4 py-3 justify-start">
        <img
          src={logo}
          alt="Encuentra logo"
          className="h-8 w-auto sm:h-8" 
        />
      </div>
    </nav>
  );
}
