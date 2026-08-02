import { Link } from "react-router-dom";

export default function LegalFooter() {
  return (
    <footer className="shrink-0 px-4 py-5 text-center text-xs text-gray-500">
      <span>Encuentra · Beta</span>
      <span aria-hidden="true" className="mx-2">·</span>
      <Link to="/privacy" className="transition hover:text-gray-900">
        Privacidad / Privacy
      </Link>
      <span aria-hidden="true" className="mx-2">·</span>
      <Link to="/terms" className="transition hover:text-gray-900">
        Términos / Terms
      </Link>
    </footer>
  );
}
