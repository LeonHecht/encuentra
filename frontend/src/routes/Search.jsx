import { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { apiFetch } from "@/hooks/useApi";
import { DEFAULT_SPACE } from "@/hooks/useSpaces";
import { supabase } from "@/lib/supabaseClient";
import SpaceSelect  from "@/components/SpaceSelect";
import SearchResultCard from "@/components/SearchResultCard";
import { useChatContextDocuments } from "@/context/ChatContextDocuments";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Search as SearchIcon } from "lucide-react";

const SEARCH_STATE_KEY = "encuentra.searchState";

function defaultSearchState() {
  return {
    q: "",
    space: DEFAULT_SPACE,
    topK: "10",
    year: "",
    results: [],
    searched: false,
  };
}

function loadSearchStateForRestore(shouldRestore) {
  try {
    if (!shouldRestore) {
      return defaultSearchState();
    }
    const raw = window.sessionStorage.getItem(SEARCH_STATE_KEY);
    if (!raw) return defaultSearchState();
    const parsed = JSON.parse(raw);
    return {
      ...defaultSearchState(),
      ...parsed,
      results: Array.isArray(parsed.results) ? parsed.results : [],
      searched: Boolean(parsed.searched),
      topK: parsed.topK ? String(parsed.topK) : "10",
    };
  } catch {
    return defaultSearchState();
  }
}

function saveSearchState(state) {
  try {
    window.sessionStorage.setItem(SEARCH_STATE_KEY, JSON.stringify(state));
  } catch {
    // Search remains usable even when session storage is unavailable.
  }
}

export default function Search() {
  const navigate = useNavigate();
  const location = useLocation();
  const { addDocument, isSelected } = useChatContextDocuments();
  const [initialSearchState] = useState(() =>
    loadSearchStateForRestore(Boolean(location.state?.restoreSearchState))
  );
  const [q, setQ]           = useState(initialSearchState.q);
  const [space, setSpace]   = useState(initialSearchState.space);
  const [topK, setTopK] = useState(initialSearchState.topK);
  const [year, setYear] = useState(initialSearchState.year);
  const [results, setResults] = useState(initialSearchState.results);
  const [searched, setSearched] = useState(initialSearchState.searched);

  useEffect(() => {
    if (!space) return;
    saveSearchState({ q, space, topK, year, results, searched });
  }, [q, space, topK, year, results, searched]);

  const [loading, setLoading] = useState(false);
  const [feedbackById, setFeedbackById] = useState({});
  const [toast, setToast] = useState({ docId: null, msg: "" });

  const onSearch = async () => {
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session) {
      navigate("/signup");
      return;
    }
    if (!q.trim()) return;
    setLoading(true);
    setSearched(true);
    try {
      const params = new URLSearchParams({
        q,
        space,
        top_k: topK,
      });
      if (year.trim()) params.set("year", year.trim());
      const res = await apiFetch("search", `?${params.toString()}`);
      setResults(res.results || []);
    } catch (err) {
      console.error("Search error:", err);
      alert("Search failed. Check console.");
    } finally {
      setLoading(false);
    }
  };

  const sendFeedback = async (docId, positive) => {
    // stub: you'll wire this up to /feedback later
    setFeedbackById((f) => ({ ...f, [docId]: positive }));
    setToast({ docId, msg: positive ? "Gracias por su feedback!" : "Gracias, vamos a mejorar!" });
    setTimeout(() => setToast({ docId: null, msg: "" }), 2000);
  };

  return (
    <div className="w-full flex-1 overflow-y-auto min-h-0 px-4 py-6 sm:px-6 lg:px-16 lg:py-8">
      <div className="mx-auto w-full max-w-6xl space-y-4">
        <h2 className="text-2xl font-semibold">Buscar casos</h2>

        <div className="mb-6 grid gap-3 rounded-lg border border-gray-200 bg-white p-3 shadow-sm sm:p-4 lg:flex lg:items-end lg:gap-4">
          <div className="min-w-0 lg:w-72 lg:shrink-0">
            <SpaceSelect
              value={space}
              onChange={(v) => setSpace(v)}
              className="h-11 w-full rounded-xl"
            />
          </div>
          <Input
            type="search"
            className="h-11 min-w-0 rounded-xl bg-background px-4 text-base shadow-sm focus-visible:border-gray-300 focus-visible:ring-0 md:text-sm lg:flex-1"
            placeholder="Ingresa las palabras de tu búsqueda..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && onSearch()}
          />
          <div className="grid grid-cols-2 gap-3 lg:contents">
            <label className="flex items-center gap-2 text-sm text-gray-600 lg:w-32 lg:shrink-0">
              <span className="shrink-0">Año</span>
              <Input
                type="number"
                inputMode="numeric"
                min="1800"
                max="2100"
                className="h-11 min-w-0 flex-1 rounded-xl bg-background px-3 text-sm shadow-sm focus-visible:border-gray-300 focus-visible:ring-0"
                placeholder="Todos"
                value={year}
                onChange={(e) => setYear(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && onSearch()}
              />
            </label>
            <label className="flex items-center gap-2 text-sm text-gray-600 lg:w-40 lg:shrink-0">
              <span className="shrink-0">Mostrar</span>
              <Select value={topK} onValueChange={setTopK}>
                <SelectTrigger className="h-11 min-w-0 flex-1 rounded-xl">
                  <SelectValue aria-label={`${topK} resultados`} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="10">10</SelectItem>
                  <SelectItem value="20">20</SelectItem>
                  <SelectItem value="50">50</SelectItem>
                </SelectContent>
              </Select>
            </label>
          </div>
          <Button
            type="button"
            onClick={onSearch}
            disabled={loading}
            variant="secondary"
            className="h-11 w-full rounded-xl bg-gray-200 px-6 text-gray-950 hover:bg-gray-300 sm:w-auto lg:min-w-32"
          >
            <SearchIcon className="h-4 w-4" aria-hidden="true" />
            {loading ? "Buscando..." : "Buscar"}
          </Button>
        </div>

        <div className="space-y-4">
          {/* ---------- 1) empty state ---------- */}
          {searched && !loading && results.length === 0 && (
            <div className="text-gray-500 italic px-2">
              No se encontraron resultados.
            </div>
          )}

          {/* ---------- 2) actual hits ---------- */}
          {results.map((res) => {
            const fb = feedbackById[res.id];
            const isToast = toast.docId === res.id;

            return (
              <div
                key={res.id}
                className="relative"
              >
                <SearchResultCard
                  result={res}
                  space={space}
                  feedback={fb}
                  onFeedback={sendFeedback}
                  onAddToChat={addDocument}
                  onOpenChat={() => navigate("/chat")}
                  isInChatContext={isSelected(space, res.id)}
                />
                {isToast && (
                  <div
                    className="
                      absolute
                      bottom-12 right-4
                      bg-white border border-gray-300
                      text-gray-800
                      px-3 py-1
                      rounded-md shadow-lg
                      animate-fade-in-out z-10
                    "
                  >
                    {toast.msg}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
