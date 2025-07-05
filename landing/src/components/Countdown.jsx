import { useEffect, useState } from 'react';

const target = new Date('2025-10-16T00:00:00-04:00').getTime(); // adjust TZ

export default function Countdown() {
  const [left, setLeft] = useState(target - Date.now());

  useEffect(() => {
    const t = setInterval(() => setLeft(target - Date.now()), 1000);
    return () => clearInterval(t);
  }, []);

  if (left <= 0) return <span className="text-primary font-semibold">¡Ya disponible!</span>;

  const s = Math.floor(left / 1000) % 60;
  const m = Math.floor(left / (1000 * 60)) % 60;
  const h = Math.floor(left / (1000 * 60 * 60)) % 24;
  const d = Math.floor(left / (1000 * 60 * 60 * 24));

  const pad = (n) => n.toString().padStart(2, '0');
  return (
    <span className="text-primary font-semibold tabular-nums">
      {d}d {pad(h)}:{pad(m)}:{pad(s)}
    </span>
  );
}
