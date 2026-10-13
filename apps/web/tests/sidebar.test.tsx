import React from "react";
import { render, screen } from "@testing-library/react";
import Sidebar from "@/components/layout/Sidebar";

// Mock next/navigation
jest.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

// Mock api-client so AuthProvider does not make real requests
jest.mock("@/lib/api-client", () => ({
  apiClient: {
    getToken: jest.fn().mockReturnValue(null),
    clearToken: jest.fn(),
    getMe: jest
      .fn()
      .mockResolvedValue({ id: "u1", name: "Dev", email: "dev@test.com" }),
  },
}));

// Import AuthProvider AFTER the mock above
import { AuthProvider } from "@/lib/auth-context";

const renderWithAuth = (ui: React.ReactElement) =>
  render(<AuthProvider>{ui}</AuthProvider>);

describe("Sidebar", () => {
  it("renders all primary navigation items", () => {
    renderWithAuth(<Sidebar />);
    expect(screen.getByText("Today")).toBeInTheDocument();
    expect(screen.getByText("AI Assistant")).toBeInTheDocument();
    expect(screen.getByText("Tasks")).toBeInTheDocument();
    expect(screen.getByText("Requirements")).toBeInTheDocument();
    expect(screen.getByText("Projects")).toBeInTheDocument();
    expect(screen.getByText("Clients")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("displays the V1 version label", () => {
    renderWithAuth(<Sidebar />);
    expect(screen.getByText("TaskMate AI v1.0.0")).toBeInTheDocument();
  });

  it("marks the Today link as active when on the root path", () => {
    renderWithAuth(<Sidebar />);
    // The Today link should exist and navigate to "/"
    const todayLink = screen.getByText("Today").closest("a");
    expect(todayLink).toHaveAttribute("href", "/");
  });
});
