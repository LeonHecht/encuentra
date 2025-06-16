import { useEffect, useState } from "react";
import { useApi } from "./useApi";
import { useAuth } from "@/context/AuthContext";
import { formatSpaceLabel } from "@/utils/formatSpaceLabel";

export function useSpaces() {
  const { user } = useAuth();                    // email, organization, …
  const [spaces, setSpaces] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    useApi("user/spaces")
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
