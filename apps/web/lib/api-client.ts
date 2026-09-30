export class ApiClient {
  private baseUrl = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') + '/api/v1';

  setToken(token: string) {
    if (typeof window !== 'undefined') {
      localStorage.setItem('taskmate_token', token);
    }
  }

  getToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('taskmate_token');
    }
    return null;
  }

  clearToken() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('taskmate_token');
    }
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  private async fetchAPI(endpoint: string, options: RequestInit = {}) {
    const token = this.getToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errorMsg = 'An error occurred';
      try {
        const errorData = await response.json();
        // Parse error.message from {error: {code, message}}
        if (errorData.error && errorData.error.message) {
          errorMsg = errorData.error.message;
        } else if (errorData.detail) {
          errorMsg = errorData.detail;
        }
      } catch (e) {
        // ignore
      }
      throw new Error(errorMsg);
    }

    // handle 204 no content
    if (response.status === 204) {
      return null;
    }

    return response.json();
  }

  // Auth
  login(data: any) {
    return this.fetchAPI('/auth/login', { method: 'POST', body: JSON.stringify(data) });
  }

  register(data: any) {
    return this.fetchAPI('/auth/register', { method: 'POST', body: JSON.stringify(data) });
  }

  getMe() {
    return this.fetchAPI('/auth/me');
  }

  updateMe(data: any) {
    return this.fetchAPI('/auth/me', { method: 'PATCH', body: JSON.stringify(data) });
  }

  // Clients
  listClients(params?: Record<string, any>) {
    const query = params ? '?' + new URLSearchParams(params as any).toString() : '';
    return this.fetchAPI(`/clients${query}`);
  }

  createClient(data: any) {
    return this.fetchAPI('/clients', { method: 'POST', body: JSON.stringify(data) });
  }

  getClient(id: string) {
    return this.fetchAPI(`/clients/${id}`);
  }

  updateClient(id: string, data: any) {
    return this.fetchAPI(`/clients/${id}`, { method: 'PATCH', body: JSON.stringify(data) });
  }

  archiveClient(id: string) {
    return this.fetchAPI(`/clients/${id}`, { method: 'DELETE' });
  }

  // Projects
  listProjects(params?: Record<string, any>) {
    const query = params ? '?' + new URLSearchParams(params as any).toString() : '';
    return this.fetchAPI(`/projects${query}`);
  }

  createProject(data: any) {
    return this.fetchAPI('/projects', { method: 'POST', body: JSON.stringify(data) });
  }

  getProject(id: string) {
    return this.fetchAPI(`/projects/${id}`);
  }

  updateProject(id: string, data: any) {
    return this.fetchAPI(`/projects/${id}`, { method: 'PATCH', body: JSON.stringify(data) });
  }

  archiveProject(id: string) {
    return this.fetchAPI(`/projects/${id}`, { method: 'DELETE' });
  }

  // Tasks
  listTasks(params?: Record<string, any>) {
    const query = params ? '?' + new URLSearchParams(params as any).toString() : '';
    return this.fetchAPI(`/tasks${query}`);
  }

  createTask(data: any) {
    return this.fetchAPI('/tasks', { method: 'POST', body: JSON.stringify(data) });
  }

  getTask(id: string) {
    return this.fetchAPI(`/tasks/${id}`);
  }

  updateTask(id: string, data: any) {
    return this.fetchAPI(`/tasks/${id}`, { method: 'PATCH', body: JSON.stringify(data) });
  }

  archiveTask(id: string) {
    return this.fetchAPI(`/tasks/${id}`, { method: 'DELETE' });
  }

  changeTaskStatus(id: string, status: string) {
    return this.fetchAPI(`/tasks/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) });
  }

  changeTaskPriority(id: string, priority: string) {
    return this.fetchAPI(`/tasks/${id}/priority`, { method: 'PATCH', body: JSON.stringify({ priority }) });
  }

  getTaskEvents(id: string) {
    return this.fetchAPI(`/tasks/${id}/events`);
  }

  // Repositories
  listProjectRepos(projectId: string) {
    return this.fetchAPI(`/projects/${projectId}/repositories`);
  }

  createRepo(projectId: string, data: any) {
    return this.fetchAPI(`/projects/${projectId}/repositories`, { method: 'POST', body: JSON.stringify(data) });
  }

  getRepo(id: string) {
    return this.fetchAPI(`/repositories/${id}`);
  }

  updateRepo(id: string, data: any) {
    return this.fetchAPI(`/repositories/${id}`, { method: 'PATCH', body: JSON.stringify(data) });
  }

  deleteRepo(id: string) {
    return this.fetchAPI(`/repositories/${id}`, { method: 'DELETE' });
  }

  // Dashboard
  getDashboardToday() {
    return this.fetchAPI('/dashboard/today');
  }

  // Labels
  listLabels() {
    return this.fetchAPI('/labels');
  }

  createLabel(data: any) {
    return this.fetchAPI('/labels', { method: 'POST', body: JSON.stringify(data) });
  }
}

export const apiClient = new ApiClient();
