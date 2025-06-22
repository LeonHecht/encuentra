import { useState } from "react";
import SpaceSelect      from "@/components/SpaceSelect";
import { useApi }       from "@/hooks/useApi";
import { createSpace }  from "@/api/createSpace";

export default function Uploads() {
  const [spacesVersion, bump] = useState(0);      // force SpaceSelect reload
  const [space,  setSpace]    = useState("");
  const [files,  setFiles]    = useState([]);
  const [msg,    setMsg]      = useState("");
  const [newName, setNewName] = useState("");     // text-box for new space
  const [creating, setCreating] = useState(false);

  /* ---------- create-space handler ---------- */
  const handleCreate = async () => {
    if (!newName.trim()) return;
    try {
      const key = await createSpace(newName.trim());
      bump((v) => v + 1);            // force SpaceSelect to fetch again
      setSpace(key);                 // pre-select the new space
      setNewName("");
      setCreating(false);
      setMsg(`Space “${key}” created. Now upload files.`);
    } catch (e) {
      setMsg("Error creating space: " + e.message);
    }
  };

  /* ---------- upload handler ---------- */
  const onSubmit = async (e) => {
    e.preventDefault();
    if (!space || space === "__new__") {
      setMsg("Choose a space first.");
      return;
    }
    if (files.length === 0) {
      setMsg("Selecciona al menos un archivo.");
      return;
    }

    const fd = new FormData();
    files.forEach((f) => fd.append("files", f));
    fd.append("space", space);

    try {
      const data = await useApi("upload", "", { method: "POST", body: fd });
      setMsg(`Subidos ${data.uploaded.length} archivo(s) en “${data.space}”.`);
      setFiles([]);
    } catch (err) {
      setMsg("Error: " + err.message);
    }
  };

  /* ---------- JSX ---------- */
  return (
    <div className="flex items-center justify-center h-screen">
      <form onSubmit={onSubmit} className="p-6 space-y-6 max-w-lg w-full rounded-3xl shadow-lg">
        <h2 className="text-2xl font-semibold">Upload documents</h2>

        {/* -------- space picker + new-space flow -------- */}
        <div className="space-y-2">
          <label className="block">Elige espacio:</label>
          <SpaceSelect
            allowCreate
            key={spacesVersion}          // reload list after creation
            value={space}
            onChange={(v) => {
              if (v === "__new__") setCreating(true);
              else { setCreating(false); setSpace(v); }
            }}
            className="p-3 bg-transparent transition border border-transparent rounded-2xl hover:border-inherit hover:bg-gray-50 hover:cursor-pointer focus:outline-none"
          />

          {creating && (
            <div className="flex gap-2 mt-2">
              <div className={`input-wrapper flex-grow relative ${newName ? 'caret-hidden' : ''}`}>
                <input
                  type="text"
                  placeholder="new-space-name"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="flex-grow w-full py-3 px-4 border rounded-2xl
                                  focus:outline-none focus:placeholder-transparent
                                  hover:bg-gray-50 transition-colors"
                />
              </div>
              <button
                type="button"
                onClick={handleCreate}
                className="px-8 py-3 bg-gray-200 text-gray-900 rounded-3xl hover:bg-gray-300 transition"
              >
                Create
              </button>
              <button
                type="button"
                onClick={() => { setCreating(false); setNewName(""); }}
                className="text-gray-600 px-2"
              >
                Cancel
              </button>
            </div>
          )}
        </div>

        {/* -------- file picker -------- */}
        <div className="space-y-2">
          <label className="block mb-1">Elige archivos:</label>
          <input
            type="file"
            multiple
            onChange={(e) => setFiles(Array.from(e.target.files))}
            className="block"
          />
        </div>

        <button
          type="submit"
          disabled={!space || space === "__new__" || files.length === 0}
          className="px-8 py-3 bg-black text-white rounded-3xl hover:bg-gray-800 transition disabled:opacity-50"
        >
          Upload {files.length > 0 && `(${files.length})`}
        </button>

        {msg && <p className="text-green-600">{msg}</p>}
      </form>
    </div>
  );
}
