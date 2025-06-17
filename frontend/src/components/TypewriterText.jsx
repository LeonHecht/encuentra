import useTypewriter from "@/hooks/useTypewriter";

/** Renders text with a typewriter effect (fake streaming). */
export default function TypewriterText({ text, speed = 25 }) {
  const visible = useTypewriter(text, speed);
  return <span>{visible}</span>;
}
