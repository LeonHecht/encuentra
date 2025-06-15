import { Routes, Route, Link } from "react-router-dom";
import Navbar from './components/Navbar';
import Landing from "./routes/Landing";
import Search from "./routes/Search";
import Chat from "./routes/Chat";
import Uploads from "./routes/Uploads";
import Login from "./routes/Login";
// import bg from './assets/landing_bg.png';

export default function App() {
  return (
    <div
      className="flex flex-col h-screen overflow-hidden"
      style={{ backgroundColor: "#F5F5F7" }}  
      // style={{
      //     backgroundImage: `url(${bg})`,
      //     backgroundSize: 'cover',
      //     backgroundPosition: 'center',
      //     backgroundRepeat: 'no-repeat',
      //   }}  
    >
      <Navbar />
      <main className="flex flex-col flex-grow overflow-hidden min-h-0 mx-auto h-full w-full">
        <Routes>
          <Route path="/"      element={<Landing />} />
          <Route path="/search"  element={<Search />} />
          <Route path="/chat"    element={<Chat />} />
          <Route path="/uploads" element={<Uploads />} />
          <Route path="/login"   element={<Login />} />
        </Routes>
      </main>
      <footer className="text-center py-2 text-sm text-gray-500 border-t">
        © 2025 encuentra
      </footer>
    </div>
  );
}