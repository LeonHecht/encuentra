import { Link } from 'react-router-dom';

export default function Navbar() {
  return (
    <nav className="bg-white shadow-md">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        <Link to="/" className="text-2xl font-bold text-indigo-600">
          encuentra
        </Link>
        <div className="space-x-4">
          <Link to="/search" className="text-gray-600 hover:text-indigo-600">
            Search
          </Link>
          <Link to="/chat" className="text-gray-600 hover:text-indigo-600">
            Chat
          </Link>
          <Link to="/uploads" className="text-gray-600 hover:text-indigo-600">
            Uploads
          </Link>
        </div>
      </div>
    </nav>
  );
}
