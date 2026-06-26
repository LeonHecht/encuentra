import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './index.css';
import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { ChatContextDocumentsProvider } from "./context/ChatContextDocuments";

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AuthProvider>
      <ChatContextDocumentsProvider>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </ChatContextDocumentsProvider>
    </AuthProvider>
  </StrictMode>,
);
