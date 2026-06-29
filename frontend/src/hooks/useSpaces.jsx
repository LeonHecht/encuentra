import { useEffect, useState } from "react";
import { apiFetch } from "./useApi";
import { useAuth } from "@/context/AuthContext";
import { formatSpaceLabel } from "@/utils/formatSpaceLabel";

export const DEFAULT_SPACE = "supreme_court";

let cachedSpaces = [DEFAULT_SPACE];
let hasLoadedSpaces = false;
let spacesRequest = null;
const listeners = new Set();

function isPublicSpace(space) {
  return typeof space === "string" && !space.includes("/");
}

function normalizeSpaces(spaces) {
  const loadedSpaces = Array.isArray(spaces) ? spaces.filter(Boolean) : [];
  const publicSpace = loadedSpaces.find(isPublicSpace) || DEFAULT_SPACE;
  const privateSpaces = loadedSpaces.filter((space) => !isPublicSpace(space));

  return [publicSpace, ...privateSpaces];
}

function notifySpacesChanged() {
  listeners.forEach((listener) => listener(cachedSpaces));
}

function loadSpacesOnce() {
  if (hasLoadedSpaces) return Promise.resolve(cachedSpaces);

  if (!spacesRequest) {
    spacesRequest = apiFetch("user/spaces")
      .then((d) => {
        cachedSpaces = normalizeSpaces(d.spaces);
        hasLoadedSpaces = true;
        notifySpacesChanged();
        return cachedSpaces;
      })
      .catch((error) => {
        console.error("Failed to fetch spaces", error);
        return cachedSpaces;
      })
      .finally(() => {
        spacesRequest = null;
      });
  }

  return spacesRequest;
}

export function useSpaces() {
  // Be resilient if used outside of AuthProvider (e.g., some tests)
  const auth = useAuth();
  const user = auth?.session?.user; // Supabase user object
  const [spaces, setSpaces] = useState(cachedSpaces);
  const [loading, setLoading] = useState(!hasLoadedSpaces);

  useEffect(() => {
    let alive = true;
    const listener = (nextSpaces) => {
      if (alive) {
        setSpaces(nextSpaces);
      }
    };

    listeners.add(listener);
    loadSpacesOnce().finally(() => {
      if (alive) {
        setLoading(false);
      }
    });

    return () => {
      alive = false;
      listeners.delete(listener);
    };
  }, []);

  return {
    spaces,
    loading,
    // handy bound formatter
    label: (s) => formatSpaceLabel(s, user ?? {}),
    user,
  };
}
