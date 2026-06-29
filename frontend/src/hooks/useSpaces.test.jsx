import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { useSpaces } from "./useSpaces";

const apiFetchMock = vi.fn();

vi.mock("./useApi", () => ({
  apiFetch: (...args) => apiFetchMock(...args),
}));

vi.mock("@/context/AuthContext", () => ({
  useAuth: () => ({
    session: {
      user: {
        email: "me@example.com",
      },
    },
  }),
}));

function SpacesProbe() {
  const { loading, spaces } = useSpaces();

  return (
    <div>
      <span>loading:{String(loading)}</span>
      <span>spaces:{spaces.join(",")}</span>
    </div>
  );
}

afterEach(() => {
  apiFetchMock.mockClear();
});

test("reuses loaded spaces when remounted", async () => {
  apiFetchMock.mockResolvedValueOnce({
    spaces: ["supreme_court", "public", "me@example.com/personal"],
  });

  const first = render(<SpacesProbe />);

  await waitFor(() => {
    expect(screen.getByText("loading:false")).toBeInTheDocument();
  });
  expect(screen.getByText("spaces:supreme_court,me@example.com/personal")).toBeInTheDocument();
  expect(apiFetchMock).toHaveBeenCalledTimes(1);

  first.unmount();
  render(<SpacesProbe />);

  expect(screen.getByText("loading:false")).toBeInTheDocument();
  expect(screen.getByText("spaces:supreme_court,me@example.com/personal")).toBeInTheDocument();
  expect(apiFetchMock).toHaveBeenCalledTimes(1);
});
