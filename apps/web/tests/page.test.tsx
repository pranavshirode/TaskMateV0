import { render, screen } from "@testing-library/react";
import Home from "@/app/page";

// Mock the api-client module
jest.mock("@/lib/api-client", () => ({
  apiClient: {
    getSystemInfo: jest.fn().mockResolvedValue({
      data: { name: "TaskMate API", version: "0.1.0", environment: "testing" },
      error: null,
    }),
  },
}));

// Mock next/navigation
jest.mock("next/navigation", () => ({
  usePathname: () => "/",
  useRouter: () => ({ push: jest.fn() }),
}));

describe("Home Page", () => {
  it("renders the welcome message", () => {
    render(<Home />);
    expect(screen.getByText("Welcome to TaskMate")).toBeInTheDocument();
  });

  it("renders the system status section", () => {
    render(<Home />);
    expect(screen.getByText("System Status")).toBeInTheDocument();
  });
});
