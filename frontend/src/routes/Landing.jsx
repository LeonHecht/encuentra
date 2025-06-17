import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

export default function Landing() {
  return (
    <div className="h-screen flex flex-col items-center justify-center text-gray-900">
      {/* Animated headline (starts centred & large; settles smaller & higher) */}
      <motion.div
        initial={{ y: +30, scale: 1.6 }}
        animate={{ y: -10, scale: 1 }}
        transition={{ type: 'spring', stiffness: 80, damping: 16, duration: 1.1 }}
        className="flex items-end"
      >
        <h1 className="text-6xl md:text-6xl font-semibold tracking-tight">encuentr.a</h1>
        <h1 className="text-6xl md:text-6xl font-semibold tracking-tight text-gray-400">i</h1>
      </motion.div>

      {/* Subtitle + buttons fade / slide in once headline settles */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.1, duration: 0.5 }}
        className="flex flex-col items-center mt-6 space-y-10"
      >
        <p className="text-xl md:text-2xl font-light text-center">
          Intelligent legal search & chat over your documents
        </p>

        <div className="flex gap-4">
          <Link
            to="/search"
            className="px-8 py-3 bg-black text-white rounded-3xl hover:bg-gray-800 transition"
          >
            Search
          </Link>
          <Link
            to="/chat"
            className="px-8 py-3 bg-gray-200 text-gray-900 rounded-3xl hover:bg-gray-300 transition"
          >
            Chat
          </Link>
        </div>
      </motion.div>
    </div>
  );
}
