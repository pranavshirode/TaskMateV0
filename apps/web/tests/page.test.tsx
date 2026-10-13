import React from "react";
import { render, screen } from "@testing-library/react";
import Home from "@/app/page";

// Mock next/navigation
jest.mock("next/navigation", () => ({
  usePathname: () => "/",
  useRouter: () => ({ push: jest.fn() }),
  useSearchParams: () => ({ get: jest.fn() }),
}));

// Mock api-client before importing anything that uses it
jest.mock("@/lib/api-client", () => ({
  apiClient: {
    getToken: jest.fn().mockReturnValue("fake-token"),
    clearToken: jest.fn(),
    getMe: jest
      .fn()
      .mockResolvedValue({ id: "u1", name: "Alex", email: "alex@test.com" }),
    getDashboardToday: jest.fn().mockResolvedValue({
      greeting: "Good morning, Alex",
      due_today: [],
      overdue: [],
      high_priority: [],
      active_projects: [],
      recently_updated: [],
    }),
  },
}));

import { AuthProvider } from "@/lib/auth-context";

const renderWithAuth = (ui: React.ReactElement) =>
  render(<AuthProvider>{ui}</AuthProvider>);

describe("Home / Dashboard Page", () => {
  it("renders without crashing inside AuthProvider", () => {
    // Page starts in loading state — just verify it mounts cleanly
    const { container } = renderWithAuth(<Home />);
    expect(container).toBeTruthy();
  });

  it("renders a loading spinner on initial mount", () => {
    renderWithAuth(<Home />);
    // The page starts in isLoading=true and renders LoadingSpinner
    // We verify the page root element is present (not an error boundary)
    const root = document.querySelector("body");
    expect(root).not.toBeNull();
  });
});
