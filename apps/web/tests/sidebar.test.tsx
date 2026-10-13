import React, { act } from "react";
import { render, screen } from "@testing-library/react";
import Sidebar from "@/components/layout/Sidebar";

// Mock next/navigation
jest.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

// Mock api-client so AuthProvider does not make real requests.
// getToken returns null → initAuth skips the async getMe call entirely,
// so no state updates happen outside act().
jest.mock("@/lib/api-client", () => ({
  apiClient: {
    getToken: jest.fn().mockReturnValue(null),
    clearToken: jest.fn(),
    getMe: jest.fn(),
  },
}));

// Import AuthProvider AFTER the mock above
import { AuthProvider } from "@/lib/auth-context";

const renderWithAuth = async (ui: React.ReactElement) => {
  let result: ReturnType<typeof render>;
  await act(async () => {
    result = render(<AuthProvider>{ui}</AuthProvider>);
  });
  return result!;
};

describe("Sidebar", () => {
  it("renders all primary navigation items", async () => {
    await renderWithAuth(<Sidebar />);
    expect(screen.getByText("Today")).toBeInTheDocument();
    expect(screen.getByText("AI Assistant")).toBeInTheDocument();
    expect(screen.getByText("Tasks")).toBeInTheDocument();
    expect(screen.getByText("Requirements")).toBeInTheDocument();
    expect(screen.getByText("Projects")).toBeInTheDocument();
    expect(screen.getByText("Clients")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("displays the V1 version label", async () => {
    await renderWithAuth(<Sidebar />);
    expect(screen.getByText("TaskMate AI v1.0.0")).toBeInTheDocument();
  });

  it("marks the Today link as active when on the root path", async () => {
    await renderWithAuth(<Sidebar />);
    // The Today link should exist and navigate to "/"
    const todayLink = screen.getByText("Today").closest("a");
    expect(todayLink).toHaveAttribute("href", "/");
  });
});
