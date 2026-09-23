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

  // ---- Future API methods (Sprint 1+) ----
  // async getTasks(): Promise<ApiResponse<Task[]>> { ... }
  // async createTask(task: CreateTaskInput): Promise<ApiResponse<Task>> { ... }
  // async updateTask(id: string, task: UpdateTaskInput): Promise<ApiResponse<Task>> { ... }
  // async getProjects(): Promise<ApiResponse<Project[]>> { ... }
  // async sendMessage(message: string): Promise<ApiResponse<AgentResponse>> { ... }
}

export const apiClient = new TaskMateApiClient();
export type { HealthResponse, ReadinessResponse, SystemInfoResponse, ApiResponse, ApiError };
