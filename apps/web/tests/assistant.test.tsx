import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import AssistantPage from "@/app/assistant/page";

// Mock the api client
jest.mock("@/lib/api-client", () => ({
  apiClient: {
    sendMessage: jest.fn(),
    getConversations: jest.fn(),
    getConversation: jest.fn(),
  },
}));

// Mock next/navigation
jest.mock("next/navigation", () => ({
  usePathname: () => "/assistant",
  useRouter: () => ({ push: jest.fn() }),
}));

describe("AssistantPage", () => {
  it("renders the AI assistant header", () => {
    render(<AssistantPage />);
    expect(screen.getByText(/TaskMate AI/i)).toBeInTheDocument();
  });

  it("renders quick action buttons", () => {
    render(<AssistantPage />);
    expect(
      screen.getByText(/What should I work on today/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/Show overdue tasks/i)).toBeInTheDocument();
    expect(screen.getByText(/Create a task/i)).toBeInTheDocument();
    expect(screen.getByText(/High-priority tasks/i)).toBeInTheDocument();
  });

  it("renders the input field", () => {
    render(<AssistantPage />);
    expect(screen.getByPlaceholderText(/Ask TaskMate/i)).toBeInTheDocument();
  });

  it("renders the send button", () => {
    render(<AssistantPage />);
    expect(screen.getByText("Send")).toBeInTheDocument();
  });

  it("send button is disabled when input is empty", () => {
    render(<AssistantPage />);
    const sendButton = screen.getByText("Send");
    expect(sendButton).toBeDisabled();
  });
});
