import { useState, useEffect } from "react";
import { apiFetch } from "@/hooks/useApi";
import SpaceSelect  from "@/components/SpaceSelect";
import SearchResultCard from "@/components/SearchResultCard";
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

export default function Search() {
  const [q, setQ]           = useState("");
  const [_spaces, setSpaces] = useState([]);
  const [space, setSpace]   = useState("");
  const [topK, setTopK] = useState("10");
  const [year, setYear] = useState("");
  const [results, setResults] = useState([]);
  const [searched, setSearched] = useState(false);
  useEffect(() => {
    apiFetch("user/spaces").then((d) => {
      const s = d.spaces || [];
      setSpaces(s);
      if (s.length > 0) setSpace(s[0]);
    }).catch((e) => console.error("Failed to fetch spaces", e));
  }, []);

  const [loading, setLoading] = useState(false);
  const [feedbackById, setFeedbackById] = useState({});
  const [toast, setToast] = useState({ docId: null, msg: "" });

  const onSearch = async () => {
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
    <div className="w-full flex-1 overflow-y-auto min-h-0 space-y-4 px-16 py-8">
      <h2 className="text-2xl font-semibold mb-4">Buscar casos</h2>

      <div className="mb-6 flex items-center gap-4">
        <SpaceSelect
          value={space}
          onChange={(v) => setSpace(v)}
          className="h-11 w-80 rounded-xl"
        />
        <Input
          type="search"
          className="h-11 flex-1 rounded-xl bg-background px-4 text-base shadow-sm focus-visible:border-gray-300 focus-visible:ring-0 md:text-sm"
          placeholder="Ingresa las palabras de tu búsqueda..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onSearch()}
        />
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span>Año</span>
          <Input
            type="number"
            inputMode="numeric"
            min="1800"
            max="2100"
            className="h-11 w-24 rounded-xl bg-background px-3 text-sm shadow-sm focus-visible:border-gray-300 focus-visible:ring-0"
            placeholder="Todos"
            value={year}
            onChange={(e) => setYear(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && onSearch()}
          />
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span>Mostrar</span>
          <Select value={topK} onValueChange={setTopK}>
            <SelectTrigger className="h-11 w-24 rounded-xl">
              <SelectValue aria-label={`${topK} resultados`} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="10">10</SelectItem>
              <SelectItem value="20">20</SelectItem>
              <SelectItem value="50">50</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <Button
          type="button"
          onClick={onSearch}
          disabled={loading}
          variant="secondary"
          className="h-11 min-w-32 rounded-xl bg-gray-200 px-6 text-gray-950 hover:bg-gray-300"
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
  );
}
