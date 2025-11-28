import { useEffect, useState } from "react";
import { apiFetch } from "./useApi";
import { useAuth } from "@/context/AuthContext";
import { formatSpaceLabel } from "@/utils/formatSpaceLabel";

export function useSpaces() {
  // Be resilient if used outside of AuthProvider (e.g., some tests)
  const auth = useAuth();
  const user = auth?.session?.user; // Supabase user object
  const [spaces, setSpaces] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch("user/spaces")
      .then((d) => setSpaces(d.spaces))
      .finally(() => setLoading(false));
  }, []);

  return {
    spaces,
    loading,
    // handy bound formatter
    label: (s) => formatSpaceLabel(s, user ?? {}),
    user,
  };
}
