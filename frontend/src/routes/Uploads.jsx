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
    <form onSubmit={onSubmit} className="p-6 space-y-4 max-w-lg">
      <h2 className="text-2xl font-semibold">Upload documents</h2>

      {/* -------- space picker + new-space flow -------- */}
      <div className="space-y-2">
        <label className="block">Select space:</label>
        <SpaceSelect
          key={spacesVersion}          // reload list after creation
          value={space}
          onChange={(v) => {
            if (v === "__new__") setCreating(true);
            else { setCreating(false); setSpace(v); }
          }}
          className="border p-2 rounded w-full"
        />

        {creating && (
          <div className="flex gap-2 mt-2">
            <input
              type="text"
              placeholder="new-space-name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="flex-1 border p-2 rounded"
            />
            <button
              type="button"
              onClick={handleCreate}
              className="bg-indigo-600 text-white px-3 rounded"
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
      <div>
        <label className="block mb-1">Choose files:</label>
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
        className="bg-indigo-600 text-white px-4 py-2 rounded disabled:opacity-50"
      >
        Upload {files.length > 0 && `(${files.length})`}
      </button>

      {msg && <p className="text-green-600">{msg}</p>}
    </form>
  );
}
