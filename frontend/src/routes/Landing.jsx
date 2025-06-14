import { Link } from "react-router-dom";

export default function Landing() {
  return (
    <div className="flex flex-col md:flex-row items-center justify-center h-screen bg-gray-900 text-white px-6 md:px-12">
      <div className="flex-1 flex flex-col items-start justify-center space-y-8 max-w-xl">
        <h1 className="text-5xl md:text-6xl font-bold">encuentra</h1>
        <p className="text-xl md:text-2xl font-light text-gray-300">
          Instant legal search & seamless chat over your documents.
        </p>

        <div className="flex gap-6">
          <Link
            to="/search"
            className="px-8 py-3 bg-indigo-600 hover:bg-indigo-700 text-white text-lg rounded-md transition"
          >
            Search
          </Link>
          <Link
            to="/chat"
            className="px-8 py-3 border border-gray-500 hover:border-white text-white text-lg rounded-md transition"
          >
            Chat
          </Link>
        </div>
      </div>

      <div className="hidden md:flex flex-1 justify-center">
        {/* Replace with your own SVG or image */}
        <img src="/scale-illustration.svg" alt="Balancing Scale" className="w-80 opacity-80" />
      </div>
    </div>
  );
}
