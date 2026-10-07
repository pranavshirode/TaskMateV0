/**
 * TaskMate API Client
 * Centralized API communication layer
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ApiResponse<T> {
  data: T | null;
  error: ApiError | null;
}

interface ApiError {
  code: string;
  message: string;
  request_id?: string;
}

interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

interface ReadinessResponse {
  status: string;
  service: string;
  version: string;
  checks: Record<string, string>;
}

interface SystemInfoResponse {
  name: string;
  version: string;
  environment: string;
}

interface AIActionResult {
  action_type: string;
  success: boolean;
  data?: Record<string, unknown>;
  error?: string;
}

interface ContextSummary {
  task_count: number;
  project_count: number;
  overdue_count: number;
  due_today_count: number;
}

interface AIChatRequest {
  message: string;
  conversation_id?: string;
}

interface AIChatResponse {
  message: string;
  intent?: string;
  confidence?: number;
  actions: AIActionResult[];
  conversation_id: string;
  context_summary?: ContextSummary;
  requires_clarification: boolean;
  suggestions: string[];
}

interface ConversationMessage {
  id: string;
  role: string;
  content: string;
  intent?: string;
  created_at: string;
}

interface Conversation {
  id: string;
  title?: string;
  created_at: string;
  updated_at: string;
  messages: ConversationMessage[];
}

interface ConversationListResponse {
  items: Conversation[];
  total: number;
}

interface AgentRunRequest {
  prompt: string;
  conversation_id?: string;
}

interface AgentRunResponse {
  conversation_id: string;
  execution_id: string;
  status: string;
  message: string;
}

interface GitHubStatusResponse {
  connected: boolean;
  username?: string;
  avatar_url?: string;
}

interface GitHubConnectRequest {
  access_token: string;
  scopes?: string;
}

// ---- Future API types (placeholders) ----
// These will be implemented in future sprints
// interface Task { id: string; title: string; status: string; ... }
// interface Project { id: string; name: string; ... }
// interface Client { id: string; name: string; ... }

class TaskMateApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<ApiResponse<T>> {
    try {
      // For local development with mock auth token
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...options?.headers as Record<string, string>,
      };
      
      // Look for a token in localStorage if running in browser
      if (typeof window !== "undefined") {
        const token = localStorage.getItem("auth_token");
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }
      }

      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        headers,
        ...options,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        return {
          data: null,
          error: errorData.error || {
            code: "REQUEST_FAILED",
            message: `Request failed with status ${response.status}`,
          },
        };
      }

      const data = await response.json();
      return { data, error: null };
    } catch (err) {
      return {
        data: null,
        error: {
          code: "NETWORK_ERROR",
          message: err instanceof Error ? err.message : "Network error occurred",
        },
      };
    }
  }

  // Health & System
  async getHealth(): Promise<ApiResponse<HealthResponse>> {
    return this.request<HealthResponse>("/health");
  }

  async getReadiness(): Promise<ApiResponse<ReadinessResponse>> {
    return this.request<ReadinessResponse>("/health/ready");
  }

  async getSystemInfo(): Promise<ApiResponse<SystemInfoResponse>> {
    return this.request<SystemInfoResponse>("/api/v1/system/info");
  }

  // AI Assistant (Sprint 2)
  async sendMessage(data: AIChatRequest): Promise<ApiResponse<AIChatResponse>> {
    return this.request<AIChatResponse>("/api/v1/ai/chat", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getConversations(): Promise<ApiResponse<ConversationListResponse>> {
    return this.request<ConversationListResponse>("/api/v1/ai/conversations");
  }

  async getConversation(id: string): Promise<ApiResponse<Conversation>> {
    return this.request<Conversation>(`/api/v1/ai/conversations/${id}`);
  }

  // AI Agent (Sprint 3)
  async runAgent(data: AgentRunRequest): Promise<ApiResponse<AgentRunResponse>> {
    return this.request<AgentRunResponse>("/api/v1/agent/run", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // Integrations (Sprint 3)
  async getGitHubStatus(): Promise<ApiResponse<GitHubStatusResponse>> {
    return this.request<GitHubStatusResponse>("/api/v1/integrations/github");
  }

  async getGitHubAuthorizeUrl(): Promise<ApiResponse<{ url: string }>> {
    return this.request<{ url: string }>("/api/v1/integrations/github/authorize");
  }

  async connectGitHub(data: GitHubConnectRequest): Promise<ApiResponse<{ status: string }>> {
    return this.request<{ status: string }>("/api/v1/integrations/github/connect", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async disconnectGitHub(): Promise<ApiResponse<{ status: string }>> {
    return this.request<{ status: string }>("/api/v1/integrations/github", {
      method: "DELETE",
    });
  }
}

export const apiClient = new TaskMateApiClient();
export type {
  HealthResponse,
  ReadinessResponse,
  SystemInfoResponse,
  ApiResponse,
  ApiError,
  AIActionResult,
  ContextSummary,
  AIChatRequest,
  AIChatResponse,
  ConversationMessage,
  Conversation,
  ConversationListResponse,
  AgentRunRequest,
  AgentRunResponse,
  GitHubStatusResponse,
  GitHubConnectRequest
};
