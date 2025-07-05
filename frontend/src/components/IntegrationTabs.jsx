import { useState } from "react";

const tabs = [
  { id: "local", label: "Subir archivos" },
  { id: "gdrive", label: "Google Drive" },
  { id: "sharepoint", label: "SharePoint" },
  { id: "onedrive", label: "OneDrive" },
  // add more here later…
];

export default function IntegrationTabs({ children }) {
  const [active, setActive] = useState("local");

  /** tiny helper passed to Uploads.jsx so it can know the tab */
  const renderView = (views) => views[active] ?? null;

  return (
    <>
      {/* ---------- tab bar ---------- */}
      <div className="mb-6 flex justify-center">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setActive(t.id)}
            className={`px-4 py-2 text-sm transition
                        ${t.id === "local" ? "rounded-l-full" : ""}
                        ${t.id === "onedrive" ? "rounded-r-full" : ""}
                        ${active === t.id
                          ? "bg-black text-white"
                          : "bg-gray-200 hover:bg-gray-300"}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ---------- injected children ---------- */}
      {children(renderView)}
    </>
  );
}
