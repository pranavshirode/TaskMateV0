// ─── Shared domain types ──────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  name: string;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
}

export interface Client {
  id: string;
  name: string;
  email?: string;
  company_name?: string;
  phone?: string;
  notes?: string;
  status?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Project {
  id: string;
  name: string;
  client_id?: string;
  status?: string;
  deadline?: string;
  start_date?: string;
  description?: string;
  task_summary?: {
    total?: number;
    completed?: number;
    in_progress?: number;
    blocked?: number;
    overdue?: number;
    [key: string]: unknown;
  };
  created_at?: string;
  updated_at?: string;
}

export interface Task {
  id: string;
  title: string;
  status: string;
  priority: string;
  project_id?: string;
  client_id?: string;
  due_date?: string;
  completed_at?: string;
  description?: string;
  estimated_minutes?: number;
  labels?: Array<{ id: string; name: string; color?: string } | string>;
  created_at?: string;
  updated_at?: string;
}

export interface TaskEvent {
  id: string;
  task_id: string;
  event_type: string;
  data?: Record<string, unknown>;
  created_at: string;
}

export interface Repository {
  id: string;
  name: string;
  url?: string;
  provider?: string;
  default_branch?: string;
  project_id?: string;
  created_at?: string;
}

export interface Label {
  id: string;
  name: string;
  color?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page?: number;
  page_size?: number;
}

export interface DashboardToday {
  greeting?: string;
  due_today: Task[];
  overdue: Task[];
  high_priority: Task[];
  active_projects: Project[];
  recently_updated: Task[];
}

export interface AIChatRequest {
  message: string;
  conversation_id?: string;
}

export interface AIChatAction {
  success: boolean;
  action_type?: string;
  type?: string;
  message?: string;
  entity?: Record<string, unknown>;
  data?: Record<string, unknown>;
  error?: string;
}

export interface AIChatResponse {
  message: string;
  conversation_id: string;
  intent?: string;
  confidence?: number;
  actions?: AIChatAction[];
  context_summary?: Record<string, unknown>;
  requires_clarification?: boolean;
  suggestions?: string[];
}

export interface Conversation {
  id: string;
  title?: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
  last_message?: string;
  messages?: unknown[];
}

export interface GitHubStatus {
  connected: boolean;
  username?: string;
  scopes?: string[];
  /** "Sign in with GitHub" is configured on the server; otherwise paste a token. */
  oauth_available?: boolean;
}

export interface GoogleStatus {
  /** The server has Google OAuth credentials. */
  configured: boolean;
  connected: boolean;
  email?: string | null;
}

export interface MCPServerStatus {
  key: string;
  label: string;
  configured: boolean;
  connected: boolean;
  account?: string | null;
  error?: string | null;
  tool_count: number;
  tools: { name: string; permission: "READ" | "WRITE" | "DESTRUCTIVE" }[];
}

export interface AgentRunRequest {
  message?: string;
  prompt?: string;
  conversation_id?: string;
}

export interface AgentPendingAction {
  step_id: string;
  tool_name: string;
  arguments: Record<string, unknown>;
  /** Human-readable description, e.g. 'Create task "Fix login" · priority HIGH' */
  summary: string;
}

export interface AgentRunResponse {
  result?: string;
  message?: string;
  conversation_id?: string;
  execution_id?: string;
  status?: string;
  pending_action?: AgentPendingAction | null;
  error?: string;
}

export interface AgentDecisionResponse {
  conversation_id: string | null;
  execution_id: string;
  status: string;
  message: string;
  result?: Record<string, unknown> | null;
}

export interface AnalysisQuestion {
  id: string;
  question_key: string;
  question: string;
  reason?: string;
  context_topic?: string;
  answer?: string;
  status: string;
}

export interface Requirement {
  id: string;
  key: string;
  category: string;
  title: string;
  description: string;
  priority: string;
  status: string;
  acceptance_criteria?: string[];
  dependencies?: string[];
  open_questions?: string[];
  /** CLIENT_STATED: explicit in the brief. AI_SUGGESTED: a recommendation to confirm with the client. */
  source?: "CLIENT_STATED" | "AI_SUGGESTED" | null;
}

export interface RequirementAssumption {
  id: string;
  description: string;
  reason?: string;
  confidence: string;
  status: string;
}

export interface RequirementRisk {
  id: string;
  description: string;
  risk_type: string;
  severity: string;
  mitigation?: string;
}

export interface RequirementsAnalysis {
  id: string;
  project_id: string;
  title: string;
  brief: string;
  status: string;
  version: number;
  approved_at?: string;
  desired_outcome?: string;
  total_requirements?: number;
  approved_requirements?: number;
  unresolved_questions?: number;
  requirements: Requirement[];
  questions: AnalysisQuestion[];
  assumptions: RequirementAssumption[];
  risks: RequirementRisk[];
  overview_data?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
}

export interface ProposedTask {
  title: string;
  description?: string;
  priority?: string;
  estimated_hours?: number;
  estimated_effort?: string;
  requirement_keys?: string[];
  linked_requirement_keys?: string[];
}

export interface TaskPlan {
  proposed_tasks: ProposedTask[];
  rationale?: string;
  estimated_total_hours?: number;
}

export interface TaskApprovalResult {
  message?: string;
  created_tasks_count: number;
  traceability_links_created: number;
  task_ids: string[];
}

export interface TraceabilityItem {
  requirement_id: string;
  requirement_key: string;
  requirement_title: string;
  key: string;
  title: string;
  status: string;
  linked_tasks: {
    id: string;
    title: string;
    status: string;
    priority: string;
  }[];
  coverage_percent: number;
}

export interface TraceabilityReport {
  total_requirements: number;
  implemented_requirements: number;
  unimplemented_requirements: number;
  overall_progress_percent: number;
  items: TraceabilityItem[];
}

export interface ProjectContextNote {
  id: string;
  title: string;
  content: string;
  category?: string;
  is_confirmed: boolean;
  is_superseded: boolean;
  created_at: string;
}

export interface ImpactSummary {
  request_id?: string;
  request_type?: string;
  classification_explanation?: string;
  scope_change_summary?: string;
  recommended_actions?: string[];
  [key: string]: unknown;
}

export interface ClientRequest {
  id: string;
  project_id: string;
  title: string;
  content: string;
  request_type: string;
  status: string;
  impact_summary?: ImpactSummary;
  created_at: string;
}

export interface AutomationExecution {
  id: string;
  project_id?: string;
  automation_type: string;
  status: string;
  result_summary?: Record<string, unknown>;
  created_at: string;
}

export interface DailySummary {
  project_id: string;
  summary: string;
  summary_text?: string;
  generated_at: string;
}

export interface Milestone {
  id: string;
  project_id: string;
  user_id: string;
  title: string;
  description?: string;
  status: string; // OPEN, IN_PROGRESS, COMPLETED, CANCELLED
  due_date?: string;
  task_count: number;
  completed_task_count: number;
  created_at: string;
  updated_at: string;
}

export interface TaskDependency {
  id: string;
  task_id: string;
  depends_on_task_id: string;
  depends_on_title?: string;
  depends_on_status?: string;
  created_at: string;
}

export interface ProposalLineItem {
  description: string;
  quantity: number;
  unit_price: number;
  total?: number;
}

export interface ProposalSection {
  heading: string;
  content: string;
}

export interface ProposalVersionSummary {
  id: string;
  version_number: number;
  change_note?: string;
  created_at: string;
}

export interface Proposal {
  id: string;
  project_id: string;
  analysis_id?: string;
  user_id: string;
  title: string;
  client_name?: string;
  executive_summary?: string;
  line_items: ProposalLineItem[];
  sections: ProposalSection[];
  currency: string;
  subtotal?: number;
  discount_percent: number;
  tax_percent: number;
  total_amount?: number;
  valid_until?: string;
  estimated_duration_weeks?: number;
  status: string; // DRAFT, PENDING_APPROVAL, SENT, ACCEPTED, REJECTED
  version: number;
  notes?: string;
  created_at: string;
  updated_at: string;
  version_history: ProposalVersionSummary[];
}

export interface ClientCommunication {
  id: string;
  client_id: string;
  project_id?: string;
  user_id: string;
  subject: string;
  content: string;
  channel: string;
  communication_type: string;
  status: string;
  scheduled_at?: string;
  approved_at?: string;
  sent_at?: string;
  notes?: string;
  client_name?: string;
  project_name?: string;
  created_at: string;
  updated_at: string;
}

export interface ClientCommunicationCreate {
  client_id: string;
  project_id?: string;
  subject: string;
  content: string;
  channel?: string;
  communication_type?: string;
  scheduled_at?: string;
  notes?: string;
}

export interface ClientCommunicationUpdate {
  subject?: string;
  content?: string;
  channel?: string;
  communication_type?: string;
  scheduled_at?: string;
  notes?: string;
  status?: string;
}

export interface AIGenerateCommunicationRequest {
  client_id: string;
  project_id?: string;
  communication_type?: string;
  tone?: string;
  context_notes?: string;
}

// ─── ApiClient ────────────────────────────────────────────────────────────────

export class ApiClient {
  private baseUrl =
    (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") + "/api/v1";

  setToken(token: string) {
    if (typeof window !== "undefined") {
      localStorage.setItem("taskmate_token", token);
    }
  }

  getToken(): string | null {
    if (typeof window !== "undefined") {
      return localStorage.getItem("taskmate_token");
    }
    return null;
  }

  clearToken() {
    if (typeof window !== "undefined") {
      localStorage.removeItem("taskmate_token");
    }
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  private async fetchAPI(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<unknown> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errorMsg = "An error occurred";
      try {
        const errorData = (await response.json()) as Record<string, unknown>;
        const errObj = errorData.error as Record<string, string> | undefined;
        if (errObj?.message) {
          errorMsg = errObj.message;
        } else if (typeof errorData.detail === "string") {
          errorMsg = errorData.detail;
        }
      } catch {
        // ignore JSON parse failures
      }
      throw new Error(errorMsg);
    }

    if (response.status === 204) {
      return null;
    }

    return response.json();
  }

  // ─── Auth ────────────────────────────────────────────────────────────────────
  login(data: LoginRequest): Promise<LoginResponse> {
    return this.fetchAPI("/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }) as Promise<LoginResponse>;
  }

  register(data: RegisterRequest): Promise<User> {
    return this.fetchAPI("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }) as Promise<User>;
  }

  getMe(): Promise<User> {
    return this.fetchAPI("/auth/me") as Promise<User>;
  }

  updateMe(data: Partial<Pick<User, "name" | "email">>): Promise<User> {
    return this.fetchAPI("/auth/me", {
      method: "PATCH",
      body: JSON.stringify(data),
    }) as Promise<User>;
  }

  // ─── Clients ─────────────────────────────────────────────────────────────────
  listClients(
    params?: Record<string, string>
  ): Promise<PaginatedResponse<Client>> {
    const query = params ? "?" + new URLSearchParams(params).toString() : "";
    return this.fetchAPI(`/clients${query}`) as Promise<
      PaginatedResponse<Client>
    >;
  }

  createClient(data: Partial<Client>): Promise<Client> {
    return this.fetchAPI("/clients", {
      method: "POST",
      body: JSON.stringify(data),
    }) as Promise<Client>;
  }

  getClient(id: string): Promise<Client> {
    return this.fetchAPI(`/clients/${id}`) as Promise<Client>;
  }

  updateClient(id: string, data: Partial<Client>): Promise<Client> {
    return this.fetchAPI(`/clients/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }) as Promise<Client>;
  }

  archiveClient(id: string): Promise<null> {
    return this.fetchAPI(`/clients/${id}`, {
      method: "DELETE",
    }) as Promise<null>;
  }

  // ─── Projects ────────────────────────────────────────────────────────────────
  listProjects(
    params?: Record<string, string>
  ): Promise<PaginatedResponse<Project>> {
    const query = params ? "?" + new URLSearchParams(params).toString() : "";
    return this.fetchAPI(`/projects${query}`) as Promise<
      PaginatedResponse<Project>
    >;
  }

  createProject(data: Partial<Project>): Promise<Project> {
    return this.fetchAPI("/projects", {
      method: "POST",
      body: JSON.stringify(data),
    }) as Promise<Project>;
  }

  getProject(id: string): Promise<Project> {
    return this.fetchAPI(`/projects/${id}`) as Promise<Project>;
  }

  updateProject(id: string, data: Partial<Project>): Promise<Project> {
    return this.fetchAPI(`/projects/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }) as Promise<Project>;
  }

  archiveProject(id: string): Promise<null> {
    return this.fetchAPI(`/projects/${id}`, {
      method: "DELETE",
    }) as Promise<null>;
  }

  // ─── Tasks ───────────────────────────────────────────────────────────────────
  listTasks(params?: Record<string, string>): Promise<PaginatedResponse<Task>> {
    const query = params ? "?" + new URLSearchParams(params).toString() : "";
    return this.fetchAPI(`/tasks${query}`) as Promise<PaginatedResponse<Task>>;
  }

  createTask(data: Partial<Task>): Promise<Task> {
    return this.fetchAPI("/tasks", {
      method: "POST",
      body: JSON.stringify(data),
    }) as Promise<Task>;
  }

  getTask(id: string): Promise<Task> {
    return this.fetchAPI(`/tasks/${id}`) as Promise<Task>;
  }

  updateTask(id: string, data: Partial<Task>): Promise<Task> {
    return this.fetchAPI(`/tasks/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }) as Promise<Task>;
  }

  archiveTask(id: string): Promise<null> {
    return this.fetchAPI(`/tasks/${id}`, { method: "DELETE" }) as Promise<null>;
  }

  changeTaskStatus(id: string, status: string): Promise<Task> {
    return this.fetchAPI(`/tasks/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }) as Promise<Task>;
  }

  changeTaskPriority(id: string, priority: string): Promise<Task> {
    return this.fetchAPI(`/tasks/${id}/priority`, {
      method: "PATCH",
      body: JSON.stringify({ priority }),
    }) as Promise<Task>;
  }

  getTaskEvents(id: string): Promise<PaginatedResponse<TaskEvent>> {
    return this.fetchAPI(`/tasks/${id}/events`) as Promise<
      PaginatedResponse<TaskEvent>
    >;
  }

  // ─── Repositories ────────────────────────────────────────────────────────────
  listProjectRepos(projectId: string): Promise<Repository[]> {
    return this.fetchAPI(`/projects/${projectId}/repositories`) as Promise<
      Repository[]
    >;
  }

  createRepo(
    projectId: string,
    data: Partial<Repository>
  ): Promise<Repository> {
    return this.fetchAPI(`/projects/${projectId}/repositories`, {
      method: "POST",
      body: JSON.stringify(data),
    }) as Promise<Repository>;
  }

  getRepo(id: string): Promise<Repository> {
    return this.fetchAPI(`/repositories/${id}`) as Promise<Repository>;
  }

  updateRepo(id: string, data: Partial<Repository>): Promise<Repository> {
    return this.fetchAPI(`/repositories/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }) as Promise<Repository>;
  }

  deleteRepo(id: string): Promise<null> {
    return this.fetchAPI(`/repositories/${id}`, {
      method: "DELETE",
    }) as Promise<null>;
  }

  // ─── Dashboard ───────────────────────────────────────────────────────────────
  getDashboardToday(): Promise<DashboardToday> {
    return this.fetchAPI("/dashboard/today") as Promise<DashboardToday>;
  }

  // ─── Labels ──────────────────────────────────────────────────────────────────
  listLabels(): Promise<Label[]> {
    return this.fetchAPI("/labels") as Promise<Label[]>;
  }

  // ─── AI ──────────────────────────────────────────────────────────────────────
  aiChat(message: string, conversationId?: string): Promise<AIChatResponse> {
    return this.fetchAPI("/ai/chat", {
      method: "POST",
      body: JSON.stringify({ message, conversation_id: conversationId }),
    }) as Promise<AIChatResponse>;
  }

  listAiConversations(): Promise<Conversation[]> {
    return this.fetchAPI("/ai/conversations") as Promise<Conversation[]>;
  }

  getAiConversation(id: string): Promise<Conversation> {
    return this.fetchAPI(`/ai/conversations/${id}`) as Promise<Conversation>;
  }

  deleteAiConversation(id: string): Promise<null> {
    return this.fetchAPI(`/ai/conversations/${id}`, {
      method: "DELETE",
    }) as Promise<null>;
  }

  getAiUsage(): Promise<Record<string, unknown>> {
    return this.fetchAPI("/ai/usage") as Promise<Record<string, unknown>>;
  }

  // ─── GitHub Integration & Agent ──────────────────────────────────────────────
  async getGitHubStatus(): Promise<{
    data: GitHubStatus | null;
    error: Error | null;
  }> {
    try {
      const data = (await this.fetchAPI(
        "/integrations/github"
      )) as GitHubStatus;
      return { data, error: null };
    } catch (e) {
      return { data: null, error: e as Error };
    }
  }

  async getGitHubAuthorizeUrl(): Promise<{
    data: { url: string } | null;
    error: Error | null;
  }> {
    try {
      const data = (await this.fetchAPI("/integrations/github/authorize")) as {
        url: string;
      };
      return { data, error: null };
    } catch (e) {
      return { data: null, error: e as Error };
    }
  }

  async connectGitHub(data: {
    code?: string;
    access_token?: string;
    state?: string;
    scopes?: string;
  }): Promise<{ data: GitHubStatus | null; error: Error | null }> {
    try {
      const res = (await this.fetchAPI("/integrations/github/connect", {
        method: "POST",
        body: JSON.stringify(data),
      })) as GitHubStatus;
      return { data: res, error: null };
    } catch (e) {
      return { data: null, error: e as Error };
    }
  }

  async disconnectGitHub(): Promise<{ data: unknown; error: Error | null }> {
    try {
      const res = await this.fetchAPI("/integrations/github", {
        method: "DELETE",
      });
      return { data: res, error: null };
    } catch (e) {
      return { data: null, error: e as Error };
    }
  }

  // ─── Google (per-user OAuth) & MCP ──────────────────────────────────────────
  getGoogleStatus(): Promise<GoogleStatus> {
    return this.fetchAPI("/integrations/google") as Promise<GoogleStatus>;
  }

  getGoogleAuthorizeUrl(): Promise<{ url: string }> {
    return this.fetchAPI("/integrations/google/authorize") as Promise<{
      url: string;
    }>;
  }

  connectGoogle(code: string, state: string): Promise<GoogleStatus> {
    return this.fetchAPI("/integrations/google/connect", {
      method: "POST",
      body: JSON.stringify({ code, state }),
    }) as Promise<GoogleStatus>;
  }

  disconnectGoogle(): Promise<unknown> {
    return this.fetchAPI("/integrations/google", { method: "DELETE" });
  }

  getMCPStatus(): Promise<MCPServerStatus[]> {
    return this.fetchAPI("/integrations/mcp") as Promise<MCPServerStatus[]>;
  }

  async runAgent(
    data: AgentRunRequest
  ): Promise<{ data: AgentRunResponse | null; error: Error | null }> {
    try {
      const res = (await this.fetchAPI("/agent/run", {
        method: "POST",
        body: JSON.stringify(data),
      })) as AgentRunResponse;
      return { data: res, error: null };
    } catch (e) {
      return { data: null, error: e as Error };
    }
  }

  /** Run (approve) or cancel (reject) the action an agent execution is waiting on. */
  decideAgentAction(
    executionId: string,
    decision: "approve" | "reject"
  ): Promise<AgentDecisionResponse> {
    return this.fetchAPI(`/agent/executions/${executionId}/${decision}`, {
      method: "POST",
    }) as Promise<AgentDecisionResponse>;
  }

  async sendMessage(data: {
    message: string;
    conversation_id?: string;
  }): Promise<{ data: AIChatResponse | null; error: Error | null }> {
    try {
      const res = await this.aiChat(data.message, data.conversation_id);
      return { data: res, error: null };
    } catch (e) {
      return { data: null, error: e as Error };
    }
  }

  // ─── Sprint 4: Requirements Analysis ─────────────────────────────────────────
  async createAnalysis(data: {
    project_id: string;
    title: string;
    brief: string;
    desired_outcome?: string;
    constraints?: string;
    deadline?: string;
  }): Promise<RequirementsAnalysis> {
    return this.fetchAPI("/requirements/", {
      method: "POST",
      body: JSON.stringify(data),
    }) as Promise<RequirementsAnalysis>;
  }

  async getAnalysis(id: string): Promise<RequirementsAnalysis> {
    return this.fetchAPI(
      `/requirements/${id}`
    ) as Promise<RequirementsAnalysis>;
  }

  async listProjectAnalyses(
    projectId: string
  ): Promise<RequirementsAnalysis[]> {
    return this.fetchAPI(`/requirements/project/${projectId}`) as Promise<
      RequirementsAnalysis[]
    >;
  }

  async analyzeBrief(analysisId: string): Promise<RequirementsAnalysis> {
    return this.fetchAPI(`/requirements/${analysisId}/analyze`, {
      method: "POST",
    }) as Promise<RequirementsAnalysis>;
  }

  async answerClarification(
    analysisId: string,
    questionId: string,
    answer: string
  ): Promise<AnalysisQuestion> {
    return this.fetchAPI(
      `/requirements/${analysisId}/questions/${questionId}/answer`,
      {
        method: "POST",
        body: JSON.stringify({ answer }),
      }
    ) as Promise<AnalysisQuestion>;
  }

  async updateRequirement(
    analysisId: string,
    reqId: string,
    data: Partial<Requirement>
  ): Promise<Requirement> {
    return this.fetchAPI(`/requirements/${analysisId}/requirements/${reqId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }) as Promise<Requirement>;
  }

  async approveAnalysis(analysisId: string): Promise<RequirementsAnalysis> {
    return this.fetchAPI(`/requirements/${analysisId}/approve`, {
      method: "POST",
    }) as Promise<RequirementsAnalysis>;
  }

  async archiveAnalysis(analysisId: string): Promise<RequirementsAnalysis> {
    return this.fetchAPI(`/requirements/${analysisId}/archive`, {
      method: "POST",
    }) as Promise<RequirementsAnalysis>;
  }

  async generateTaskPlan(analysisId: string): Promise<TaskPlan> {
    return this.fetchAPI(`/requirements/${analysisId}/generate-task-plan`, {
      method: "POST",
    }) as Promise<TaskPlan>;
  }

  async approveTaskPlan(
    analysisId: string,
    selectedTasks: ProposedTask[]
  ): Promise<TaskApprovalResult> {
    return this.fetchAPI(`/requirements/${analysisId}/approve-task-plan`, {
      method: "POST",
      body: JSON.stringify({ selected_tasks: selectedTasks }),
    }) as Promise<TaskApprovalResult>;
  }

  async getTraceability(analysisId: string): Promise<TraceabilityReport> {
    return this.fetchAPI(
      `/requirements/${analysisId}/traceability`
    ) as Promise<TraceabilityReport>;
  }

  // ─── Sprint 4: Project Context Notes & Memory ─────────────────────────────────
  async listProjectContextNotes(
    projectId: string,
    includeSuperseded = false
  ): Promise<ProjectContextNote[]> {
    return this.fetchAPI(
      `/projects/${projectId}/context?include_superseded=${includeSuperseded}`
    ) as Promise<ProjectContextNote[]>;
  }

  async createProjectContextNote(
    projectId: string,
    data: Partial<ProjectContextNote>
  ): Promise<ProjectContextNote> {
    return this.fetchAPI(`/projects/${projectId}/context`, {
      method: "POST",
      body: JSON.stringify(data),
    }) as Promise<ProjectContextNote>;
  }

  async updateProjectContextNote(
    noteId: string,
    data: Partial<ProjectContextNote>
  ): Promise<ProjectContextNote> {
    return this.fetchAPI(`/context/${noteId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }) as Promise<ProjectContextNote>;
  }

  async deleteProjectContextNote(noteId: string): Promise<null> {
    return this.fetchAPI(`/context/${noteId}`, {
      method: "DELETE",
    }) as Promise<null>;
  }

  // ─── Sprint 4: Client Requests ────────────────────────────────────────────────
  async listProjectClientRequests(projectId: string): Promise<ClientRequest[]> {
    return this.fetchAPI(`/projects/${projectId}/client-requests`) as Promise<
      ClientRequest[]
    >;
  }

  async createClientRequest(
    projectId: string,
    data: Partial<ClientRequest>
  ): Promise<ClientRequest> {
    return this.fetchAPI(`/projects/${projectId}/client-requests`, {
      method: "POST",
      body: JSON.stringify(data),
    }) as Promise<ClientRequest>;
  }

  async getClientRequest(requestId: string): Promise<ClientRequest> {
    return this.fetchAPI(
      `/client-requests/${requestId}`
    ) as Promise<ClientRequest>;
  }

  async analyzeClientRequestImpact(requestId: string): Promise<ClientRequest> {
    return this.fetchAPI(`/client-requests/${requestId}/analyze-impact`, {
      method: "POST",
    }) as Promise<ClientRequest>;
  }

  async approveClientRequest(requestId: string): Promise<ClientRequest> {
    return this.fetchAPI(`/client-requests/${requestId}/approve`, {
      method: "POST",
    }) as Promise<ClientRequest>;
  }

  // ─── Sprint 4: Automations ────────────────────────────────────────────────────
  async generateDailyProjectSummary(projectId: string): Promise<DailySummary> {
    return this.fetchAPI(`/automations/projects/${projectId}/daily-summary`, {
      method: "POST",
    }) as Promise<DailySummary>;
  }

  async syncProjectTaskConsistency(
    projectId: string
  ): Promise<Record<string, unknown>> {
    return this.fetchAPI(
      `/automations/projects/${projectId}/sync-consistency`,
      {
        method: "POST",
      }
    ) as Promise<Record<string, unknown>>;
  }

  async listAutomationExecutions(
    projectId?: string
  ): Promise<AutomationExecution[]> {
    const query = projectId ? `?project_id=${projectId}` : "";
    return this.fetchAPI(`/automations/executions${query}`) as Promise<
      AutomationExecution[]
    >;
  }

  // ─── Milestones ─────────────────────────────────────────────────────────────
  async createMilestone(data: {
    project_id: string;
    title: string;
    description?: string;
    status?: string;
    due_date?: string;
  }): Promise<Milestone> {
    return this.fetchAPI("/milestones", {
      method: "POST",
      body: JSON.stringify(data),
    }) as Promise<Milestone>;
  }

  async listProjectMilestones(projectId: string): Promise<Milestone[]> {
    return this.fetchAPI(`/milestones/project/${projectId}`) as Promise<Milestone[]>;
  }

  async getMilestone(milestoneId: string): Promise<Milestone> {
    return this.fetchAPI(`/milestones/${milestoneId}`) as Promise<Milestone>;
  }

  async updateMilestone(
    milestoneId: string,
    data: {
      title?: string;
      description?: string;
      status?: string;
      due_date?: string;
    }
  ): Promise<Milestone> {
    return this.fetchAPI(`/milestones/${milestoneId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }) as Promise<Milestone>;
  }

  async deleteMilestone(milestoneId: string): Promise<void> {
    await this.fetchAPI(`/milestones/${milestoneId}`, { method: "DELETE" });
  }

  // ─── Task Dependencies ──────────────────────────────────────────────────────
  async addTaskDependency(
    taskId: string,
    dependsOnTaskId: string
  ): Promise<TaskDependency> {
    return this.fetchAPI(`/tasks/${taskId}/dependencies`, {
      method: "POST",
      body: JSON.stringify({ depends_on_task_id: dependsOnTaskId }),
    }) as Promise<TaskDependency>;
  }

  async getTaskDependencies(taskId: string): Promise<TaskDependency[]> {
    return this.fetchAPI(`/tasks/${taskId}/dependencies`) as Promise<TaskDependency[]>;
  }

  async removeTaskDependency(
    taskId: string,
    dependsOnTaskId: string
  ): Promise<void> {
    await this.fetchAPI(`/tasks/${taskId}/dependencies/${dependsOnTaskId}`, {
      method: "DELETE",
    });
  }

  // ─── Proposals ──────────────────────────────────────────────────────────────
  async createProposal(data: {
    project_id: string;
    title: string;
    analysis_id?: string;
    client_name?: string;
    executive_summary?: string;
    line_items?: ProposalLineItem[];
    sections?: ProposalSection[];
    currency?: string;
    discount_percent?: number;
    tax_percent?: number;
    valid_until?: string;
    estimated_duration_weeks?: number;
    notes?: string;
  }): Promise<Proposal> {
    return this.fetchAPI("/proposals", {
      method: "POST",
      body: JSON.stringify(data),
    }) as Promise<Proposal>;
  }

  async listProjectProposals(projectId: string): Promise<Proposal[]> {
    return this.fetchAPI(`/proposals/project/${projectId}`) as Promise<Proposal[]>;
  }

  async getProposal(proposalId: string): Promise<Proposal> {
    return this.fetchAPI(`/proposals/${proposalId}`) as Promise<Proposal>;
  }

  async updateProposal(
    proposalId: string,
    data: Partial<Proposal>
  ): Promise<Proposal> {
    return this.fetchAPI(`/proposals/${proposalId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }) as Promise<Proposal>;
  }

  async transitionProposalStatus(
    proposalId: string,
    status: string,
    note?: string
  ): Promise<Proposal> {
    return this.fetchAPI(`/proposals/${proposalId}/transition`, {
      method: "POST",
      body: JSON.stringify({ status, note }),
    }) as Promise<Proposal>;
  }

  async deleteProposal(proposalId: string): Promise<void> {
    await this.fetchAPI(`/proposals/${proposalId}`, { method: "DELETE" });
  }

  async generateAIProposal(data: {
    project_id: string;
    analysis_id?: string;
    title: string;
    currency?: string;
    discount_percent?: number;
    tax_percent?: number;
    client_name?: string;
  }): Promise<Proposal> {
    return this.fetchAPI("/proposals/ai-generate", {
      method: "POST",
      body: JSON.stringify(data),
    }) as Promise<Proposal>;
  }

  async getProposalMarkdown(proposalId: string): Promise<string> {
    const res = await fetch(`${this.baseUrl}/proposals/${proposalId}/markdown`, {
      headers: this.getToken() ? { Authorization: `Bearer ${this.getToken()}` } : {},
    });
    if (!res.ok) throw new Error("Failed to download markdown");
    return res.text();
  }

  // ── Client Communications ──────────────────────────────────────────────────

  async listClientCommunications(
    clientId: string,
    params?: { project_id?: string; status?: string }
  ): Promise<ClientCommunication[]> {
    const qs = new URLSearchParams();
    if (params?.project_id) qs.set("project_id", params.project_id);
    if (params?.status) qs.set("status", params.status);
    const query = qs.toString() ? `?${qs.toString()}` : "";
    return this.fetchAPI(`/clients/${clientId}/communications${query}`) as Promise<ClientCommunication[]>;
  }

  async createClientCommunication(data: ClientCommunicationCreate): Promise<ClientCommunication> {
    return this.fetchAPI("/client-communications", {
      method: "POST",
      body: JSON.stringify(data),
    }) as Promise<ClientCommunication>;
  }

  async getClientCommunication(id: string): Promise<ClientCommunication> {
    return this.fetchAPI(`/client-communications/${id}`) as Promise<ClientCommunication>;
  }

  async updateClientCommunication(
    id: string,
    data: ClientCommunicationUpdate
  ): Promise<ClientCommunication> {
    return this.fetchAPI(`/client-communications/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }) as Promise<ClientCommunication>;
  }

  async approveClientCommunication(id: string): Promise<ClientCommunication> {
    return this.fetchAPI(`/client-communications/${id}/approve`, {
      method: "POST",
    }) as Promise<ClientCommunication>;
  }

  async sendClientCommunication(id: string): Promise<ClientCommunication> {
    return this.fetchAPI(`/client-communications/${id}/send`, {
      method: "POST",
    }) as Promise<ClientCommunication>;
  }

  async transitionCommunicationStatus(
    id: string,
    status: string,
    notes?: string
  ): Promise<ClientCommunication> {
    return this.fetchAPI(`/client-communications/${id}/status`, {
      method: "POST",
      body: JSON.stringify({ status, notes }),
    }) as Promise<ClientCommunication>;
  }

  async deleteClientCommunication(id: string): Promise<void> {
    await this.fetchAPI(`/client-communications/${id}`, { method: "DELETE" });
  }

  async aiDraftCommunication(data: AIGenerateCommunicationRequest): Promise<ClientCommunication> {
    return this.fetchAPI("/client-communications/ai-draft", {
      method: "POST",
      body: JSON.stringify(data),
    }) as Promise<ClientCommunication>;
  }
}

export const apiClient = new ApiClient();
