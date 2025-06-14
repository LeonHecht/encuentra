/**
 * Llama al endpoint de la API en /v1/{path}{params}
 * @param {string} path   Ruta tras /v1/, p.ej. "search" o "chat"
 * @param {string} params Query string, p.ej. "?q=delito&space=supreme_court"
 * @returns {Promise<any>}  JSON parseado
 */
export const useApi = (path, params = "", options = {}) => {
  const raw = localStorage.getItem("auth");
  const token = raw ? JSON.parse(raw).token : null;

  const headers = { ...(options.headers || {}) };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  return fetch(`http://localhost:8000/v1/${path}${params}`, {
    ...options,
    headers,
  }).then((res) => {
    if (!res.ok) throw new Error(`API error ${res.status}`);
    return res.json();
  });
};
