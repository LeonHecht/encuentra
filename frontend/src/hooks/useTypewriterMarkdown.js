// src/hooks/useTypewriterMarkdown.js
import { useState, useEffect } from "react";

export default function useTypewriterMarkdown(fullText, speed = 10) {
  const [partial, setPartial] = useState("");

  useEffect(() => {
    let i = 0;
    const id = setInterval(() => {
      setPartial(fullText.slice(0, ++i));
      if (i >= fullText.length) clearInterval(id);
    }, speed);
    return () => clearInterval(id);
  }, [fullText, speed]);

  return partial;
}
