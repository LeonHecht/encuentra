import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import logo from '../assets/logo_full-removebg.png'; // or .png

export default function Navbar() {
  const { user } = useAuth();

  const initial = user?.first_name?.[0] || user?.email?.[0];

  return (
    <nav className="shadow-md">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        <Link to="/" className="flex items-center hover:opacity-80 transition scale-95">
          <img src={logo} alt="Encuentra logo" className="w-32" />
        </Link>
        <div className="space-x-4 flex items-center">
          <Link to="/search" className="text-gray-600 hover:text-indigo-600">
            Search
          </Link>
          <Link to="/chat" className="text-gray-600 hover:text-indigo-600">
            Chat
          </Link>
          <Link to="/uploads" className="text-gray-600 hover:text-indigo-600">
            Uploads
          </Link>
          {user ? (
            <div className="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center">
              {initial?.toUpperCase()}
            </div>
          ) : (
            <Link to="/login" className="text-gray-600 hover:text-indigo-600">
              Login
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}
