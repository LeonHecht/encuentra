import { useState, useEffect } from "react";

export default function useTypewriter(fullText, speed = 25) {
  const [visible, setVisible] = useState("");

  useEffect(() => {
    if (!fullText) return setVisible("");

    let i = 0;
    const id = setInterval(() => {
      i++;
      setVisible(fullText.slice(0, i));
      if (i >= fullText.length) clearInterval(id);
    }, speed);

    return () => clearInterval(id);
  }, [fullText, speed]);

  return visible;
}
