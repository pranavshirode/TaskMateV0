import { render, screen } from "@testing-library/react";
import Sidebar from "@/components/layout/Sidebar";

jest.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

describe("Sidebar", () => {
  it("renders all navigation items", () => {
    render(<Sidebar />);
    expect(screen.getByText("Today")).toBeInTheDocument();
    expect(screen.getByText("Tasks")).toBeInTheDocument();
    expect(screen.getByText("Projects")).toBeInTheDocument();
    expect(screen.getByText("Clients")).toBeInTheDocument();
    expect(screen.getByText("Agent")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("shows Agent as disabled", () => {
    render(<Sidebar />);
    expect(screen.getByText("Soon")).toBeInTheDocument();
  });
});
