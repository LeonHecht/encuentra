/**
 * Llama al endpoint de la API en /v1/{path}{params}
 * @param {string} path   Ruta tras /v1/, p.ej. "search" o "chat"
 * @param {string} params Query string, p.ej. "?q=delito&space=supreme_court"
 * @returns {Promise<any>}  JSON parseado
 */
export const useApi = (path, params = "") =>
  fetch(`http://localhost:8000/v1/${path}${params}`)
    .then((res) => {
      if (!res.ok) throw new Error(`API error ${res.status}`);
      return res.json();
    });