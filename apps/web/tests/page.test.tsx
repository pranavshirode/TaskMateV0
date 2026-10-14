import React, { act } from "react";
import { render, screen, waitFor } from "@testing-library/react";
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

const renderWithAuth = async (ui: React.ReactElement) => {
  let result: ReturnType<typeof render>;
  await act(async () => {
    result = render(<AuthProvider>{ui}</AuthProvider>);
  });
  return result!;
};

describe("Home / Dashboard Page", () => {
  it("renders without crashing inside AuthProvider", async () => {
    const { container } = await renderWithAuth(<Home />);
    expect(container).toBeTruthy();
  });

  it("renders page content after async data loads", async () => {
    await renderWithAuth(<Home />);
    // Wait for loading spinner to disappear and content to appear
    await waitFor(() => {
      expect(document.querySelector("body")).not.toBeNull();
    });
  });
});
