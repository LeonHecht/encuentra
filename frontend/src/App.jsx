import { Routes, Route, Link } from "react-router-dom";
import Landing from "./routes/Landing";
import Search from "./routes/Search";
import Chat from "./routes/Chat";
import Uploads from "./routes/Uploads";

export default function App() {
  return (
    <>
      <nav className="p-4 bg-white shadow">
        <Link to="/" className="mr-4">Home</Link>
        <Link to="/search" className="mr-4">Search</Link>
        <Link to="/chat">Chat</Link>
        <Link to="/uploads">Uploads</Link>
      </nav>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/search" element={<Search />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/uploads" element={<Uploads />} />
      </Routes>
    </>
  );
}
