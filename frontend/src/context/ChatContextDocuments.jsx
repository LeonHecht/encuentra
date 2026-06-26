import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

const STORAGE_KEY = "encuentra.chatContextDocuments";
const fallbackContext = {
  documents: [],
  addDocument: (_doc) => {},
  removeDocument: (_space, _id) => {},
  clearDocuments: () => {},
  isSelected: (_space, _id) => false,
};
const ChatContextDocumentsContext = createContext(fallbackContext);

function documentKey(doc) {
  return `${doc.space || ""}:${doc.id || ""}`;
}

function normalizeDocument(doc) {
  if (!doc?.id || !doc?.space) return null;
  return {
    id: String(doc.id),
    space: String(doc.space),
    title: doc.title ? String(doc.title) : null,
    case_year: doc.case_year ?? null,
    download_url: doc.download_url || null,
  };
}

function loadStoredDocuments() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.map(normalizeDocument).filter(Boolean);
  } catch {
    return [];
  }
}

export function ChatContextDocumentsProvider({ children }) {
  const [documents, setDocuments] = useState(loadStoredDocuments);

  useEffect(() => {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(documents));
    } catch {
      // Ignore storage errors; the in-memory tray still works for this session.
    }
  }, [documents]);

  const addDocument = useCallback((doc) => {
    const normalized = normalizeDocument(doc);
    if (!normalized) return;
    setDocuments((prev) => {
      const key = documentKey(normalized);
      if (prev.some((item) => documentKey(item) === key)) return prev;
      return [...prev, normalized];
    });
  }, []);

  const removeDocument = useCallback((space, id) => {
    const key = documentKey({ space, id });
    setDocuments((prev) => prev.filter((doc) => documentKey(doc) !== key));
  }, []);

  const clearDocuments = useCallback(() => {
    setDocuments([]);
  }, []);

  const isSelected = useCallback(
    (space, id) => documents.some((doc) => documentKey(doc) === documentKey({ space, id })),
    [documents]
  );

  const value = useMemo(
    () => ({ documents, addDocument, removeDocument, clearDocuments, isSelected }),
    [documents, addDocument, removeDocument, clearDocuments, isSelected]
  );

  return (
    <ChatContextDocumentsContext.Provider value={value}>
      {children}
    </ChatContextDocumentsContext.Provider>
  );
}

export function useChatContextDocuments() {
  return useContext(ChatContextDocumentsContext);
}
