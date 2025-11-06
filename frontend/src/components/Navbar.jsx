import { Link, useNavigate } from 'react-router-dom';
import { useLayoutEffect, useRef, useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import logo from '../assets/logo_full-removebg.png';

export default function Navbar() {
  const { session } = useAuth();
  const user = session?.user;
  const navRef = useRef(null);
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const menuRef = useRef(null);

  // const firstName = user?.user_metadata?.first_name
  // console.log("first", firstName);
  
  // const lastName = user?.user_metadata?.last_name
  // console.log("last", lastName);

  const fullName = user?.user_metadata?.full_name;

  const initial = fullName?.[0] || user?.email?.[0];

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

  // Close dropdown on outside click or escape
  useEffect(() => {
    if (!open) return;
    const onDocClick = (e) => {
      if (!menuRef.current) return;
      if (!menuRef.current.contains(e.target)) setOpen(false);
    };
    const onEsc = (e) => { if (e.key === 'Escape') setOpen(false); };
    document.addEventListener('mousedown', onDocClick);
    document.addEventListener('keydown', onEsc);
    return () => {
      document.removeEventListener('mousedown', onDocClick);
      document.removeEventListener('keydown', onEsc);
    };
  }, [open]);

  async function handleLogout() {
    try {
      // Clear any legacy token used by API
      try { localStorage.removeItem('auth'); } catch {}
      const { supabase } = await import('../lib/supabaseClient');
      await supabase.auth.signOut();
    } catch {}
    setOpen(false);
    navigate('/login');
  }

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
            <div className="relative" ref={menuRef}>
              <button
                className="w-8 h-8 rounded-full bg-indigo-500 text-white flex items-center justify-center hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                onClick={() => setOpen((v) => !v)}
                aria-haspopup="menu"
                aria-expanded={open}
              >
                {initial?.toUpperCase()}
              </button>
              {open && (
                <div className="absolute right-0 mt-2 w-56 bg-white rounded-md shadow-lg ring-1 ring-black/5 py-1">
                  <div className="px-4 py-2 text-sm text-gray-700 border-b">
                    <div className="font-medium line-clamp-1">{fullName}</div>
                    <div className="text-gray-500 text-xs line-clamp-1">{user.email}</div>
                  </div>
                  {/* Read-only info only; removed profile & billing navigation per new requirements */}
                  <button
                    className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                    onClick={handleLogout}
                  >
                    Cerrar sesión
                  </button>
                </div>
              )}
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
