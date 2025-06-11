// frontend/src/routes/Uploads.jsx
import { useState } from "react";

export default function Uploads() {
  const [file, setFile] = useState(null);
  const [space, setSpace] = useState("default");
  const [msg, setMsg] = useState("");

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    fd.append("space", space);
    const res = await fetch("http://localhost:8000/v1/upload", {
      method: "POST",
      body: fd,
    });
    const data = await res.json();
    setMsg(`Uploaded ${data.filename} to ${data.space}`);
  };

  return (
    <form onSubmit={onSubmit} className="p-6 space-y-4">
      <h2 className="text-2xl font-semibold">Upload Document</h2>
      <input
        type="text"
        value={space}
        onChange={(e) => setSpace(e.target.value)}
        className="border p-2 rounded"
        placeholder="Space name"
      />
      <input
        type="file"
        onChange={(e) => setFile(e.target.files[0])}
        className="block"
      />
      <button className="bg-gray-800 text-white px-4 py-2 rounded">
        Upload
      </button>
      {msg && <p className="text-green-600">{msg}</p>}
    </form>
  );
}
