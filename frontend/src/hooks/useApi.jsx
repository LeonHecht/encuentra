import { supabase } from "../lib/supabaseClient";

/**
 * Llama al endpoint de la API en /v1/{path}{params}
 * @param {string} path   Ruta tras /v1/, p.ej. "search" o "chat"
 * @param {string} params Query string, p.ej. "?q=delito&space=supreme_court"
 * @returns {Promise<any>}  JSON parseado
 */
export const apiFetch = async (path, params = "", options = {}) => {
  const { data: { session } } = await supabase.auth.getSession();
  const token = session?.access_token;

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

// Back-compat named export; avoid using this name in app code to satisfy eslint-hooks
export { apiFetch as useApi };
export default apiFetch;
