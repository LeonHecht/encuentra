import { apiFetch } from "../hooks/useApi";

export async function createSpace(name) {
  // returns the canonical key, e.g. "alice@gmail.com/personal-stuff"
  const data = await apiFetch("user/spaces", "", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  return data.space;        // backend:  { "space": "<key>" }
}
