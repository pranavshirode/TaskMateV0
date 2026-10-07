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
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        headers: {
          "Content-Type": "application/json",
          ...options?.headers,
        },
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

  // AI Assistant
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

  // ---- Future API methods (Sprint 1+) ----
  // async getTasks(): Promise<ApiResponse<Task[]>> { ... }
  // async createTask(task: CreateTaskInput): Promise<ApiResponse<Task>> { ... }
  // async updateTask(id: string, task: UpdateTaskInput): Promise<ApiResponse<Task>> { ... }
  // async getProjects(): Promise<ApiResponse<Project[]>> { ... }
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
  ConversationListResponse
};
