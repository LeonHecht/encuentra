import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import LegalFooter from "@/components/LegalFooter";
import PrivacyPolicy from "./PrivacyPolicy";
import TermsOfService from "./TermsOfService";

describe("public legal content", () => {
  it("renders the privacy policy and switches languages", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <PrivacyPolicy />
      </MemoryRouter>
    );

    expect(
      screen.getByRole("heading", { level: 1, name: "Privacy Policy" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 2, name: /Artificial intelligence/ })
    ).toBeInTheDocument();
    expect(screen.getByText(/Riehlstraße 16C/)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Español" }));

    expect(
      screen.getByRole("heading", { level: 1, name: "Política de privacidad" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 2, name: /Inteligencia artificial/ })
    ).toBeInTheDocument();
  });

  it("renders beta terms with the legal-information disclaimer", () => {
    render(
      <MemoryRouter>
        <TermsOfService />
      </MemoryRouter>
    );

    expect(
      screen.getByRole("heading", { level: 1, name: "Terms of Service" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 2, name: /Research, not legal advice/ })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 2, name: /Governing law and jurisdiction/ })
    ).toBeInTheDocument();
  });

  it("exposes stable privacy and terms links", () => {
    render(
      <MemoryRouter>
        <LegalFooter />
      </MemoryRouter>
    );

    expect(screen.getByRole("link", { name: "Privacidad / Privacy" })).toHaveAttribute(
      "href",
      "/privacy"
    );
    expect(screen.getByRole("link", { name: "Términos / Terms" })).toHaveAttribute(
      "href",
      "/terms"
    );
  });
});
