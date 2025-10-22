import { Link } from 'react-router-dom';
import { useLayoutEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import logo from '../assets/logo_full-removebg.png';

export default function Navbar() {
  const { session } = useAuth();
  const user = session?.user;
  const navRef = useRef(null);

  const fullName = user?.user_metadata?.full_name;
  const firstName = user?.user_metadata?.first_name || fullName?.split(' ')[0];
  const initial = firstName?.[0] || user?.email?.[0];

  useLayoutEffect(() => {
    const el = navRef.current;
    if (!el) return;

    const setVar = () => {
      const h = el.offsetHeight || 64;
      document.documentElement.style.setProperty("--navbar-h", `${h}px`);
    };

    setVar();
    const ro = new ResizeObserver(setVar);
    ro.observe(el);
    window.addEventListener("resize", setVar);

    return () => {
      ro.disconnect();
      window.removeEventListener("resize", setVar);
    };
  }, []);

  return (
    <nav ref={navRef} className="bg-white shadow-md z-30 relative">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between max-w-full">
        <Link to="/" className="flex items-center hover:opacity-80 transition scale-95">
          <img src={logo} alt="Encuentra logo" className="w-32" />
        </Link>
        <div className="space-x-4 flex items-center">
          <Link to="/search" className="text-gray-600 hover:text-gray-700">
            Buscar
          </Link>
          <Link to="/chat" className="text-gray-600 hover:text-gray-700">
            Chat
          </Link>
          <Link to="/uploads" className="text-gray-600 hover:text-gray-700">
            Subir
          </Link>
          {user ? (
            <div className="w-8 h-8 rounded-full bg-indigo-500 text-white flex items-center justify-center">
              {initial?.toUpperCase()}
            </div>
          ) : (
            <Link to="/login" className="text-gray-600 hover:text-gray-400">
              Login
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}
