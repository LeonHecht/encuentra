import { useState } from "react";
import { useApi } from "../hooks/useApi";

const SPACE_OPTIONS = [
  { value: "supreme_court", label: "Supreme Court" },
  { value: "my_uploads",    label: "My Uploads"    },
  // add more when you have them…
];

export default function Search() {
  const [q, setQ] = useState("");
  const [space, setSpace] = useState(SPACE_OPTIONS[0].value);
  const [data, setData] = useState(null);

  const onSearch = async () => {
    if (!q) return;
    const result = await useApi("search", `?q=${encodeURIComponent(q)}`);
    setData(result);
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-semibold mb-4">Buscar casos</h2>

      <div className="flex items-center mb-4 space-x-4">
        <select
          className="border p-2 rounded"
          value={space}
          onChange={(e) => setSpace(e.target.value)}
        >
          {SPACE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        <input
          type="text"
          className="flex-grow border p-2 rounded-l"
          placeholder="Palabra clave…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <button
          onClick={onSearch}
          className="bg-teal-600 text-white p-2 rounded-r hover:bg-teal-700"
        >
          Buscar
        </button>
      </div>

      {data && (
        <table className="w-full table-auto border-collapse">
          …
        </table>
      )}
    </div>
  );
}