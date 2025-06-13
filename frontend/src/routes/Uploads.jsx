// frontend/src/routes/Uploads.jsx
import { useState } from "react";

export default function Uploads() {
  const [space, setSpace] = useState("default");
  const [files, setFiles] = useState([]);
  const [msg, setMsg] = useState("");

  const onSubmit = async (e) => {
    e.preventDefault();
    if (files.length === 0) {
      setMsg("Selecciona al menos un archivo.");
      return;
    }

    const fd = new FormData();
    files.forEach((file) => fd.append("files", file));
    fd.append("space", space);

    try {
        const res = await fetch("http://localhost:8000/v1/upload", {
          method: "POST",
          body: fd,
        });
        if (!res.ok) {
          const err = await res.text();
          throw new Error(err || res.statusText);
        }
        const data = await res.json();
        setMsg(`Subidos ${data.uploaded.length} archivos en espacio “${data.space}”.`);
      } catch (err) {
        console.error("Upload error:", err);
        setMsg(`Error: ${err.message}`);
      }
    };

  return (
    <form onSubmit={onSubmit} className="p-6 space-y-4">
      <h2 className="text-2xl font-semibold">Upload Documents</h2>

      <div>
        <label className="block mb-1">Space name:</label>
        <input
          type="text"
          value={space}
          onChange={(e) => setSpace(e.target.value)}
          className="border p-2 rounded w-full"
          placeholder="e.g. default or practice-area"
        />
      </div>

      <div>
        <label className="block mb-1">Select files:</label>
        <input
          type="file"
          multiple
          onChange={(e) => setFiles(Array.from(e.target.files))}
          className="block"
        />
      </div>

      <button
        type="submit"
        className="bg-gray-800 text-white px-4 py-2 rounded hover:bg-gray-700"
      >
        Upload {files.length > 0 && `(${files.length})`}
      </button>

      {msg && (
        <p className="mt-2 text-green-600">{msg}</p>
      )}
    </form>
  );
}