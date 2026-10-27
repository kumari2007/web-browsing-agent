import { 
  TaskState, 
  MetricsSummary, 
  ExperienceEntry, 
  KnowledgeDocument, 
  KnowledgeSearchResult, 
  SafetyStatus, 
  InterventionRequest, 
  SystemHealth 
} from '../types';

const API_BASE = '/api';

class ApiService {
  async getHealth(): Promise<SystemHealth> {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
  }

  async getConfig(): Promise<Record<string, any>> {
    const res = await fetch(`${API_BASE}/config`);
    if (!res.ok) throw new Error('Failed to fetch config');
    return res.json();
  }

  async updateConfig(payload: Record<string, any>): Promise<any> {
    const res = await fetch(`${API_BASE}/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Failed to update config');
    return res.json();
  }

  // --- Tasks ---
  async createTask(params: {
    query: string;
    start_url?: string;
    max_inspect_pages?: number;
    max_depth?: number;
    headless?: boolean;
    risk_preference?: string;
    extraction_fields?: string[];
  }): Promise<{ task_id: string; status: string; message: string }> {
    const res = await fetch(`${API_BASE}/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to create task' }));
      throw new Error(err.detail || 'Task creation failed');
    }
    return res.json();
  }

  async listTasks(limit: number = 50): Promise<TaskState[]> {
    const res = await fetch(`${API_BASE}/tasks?limit=${limit}`);
    if (!res.ok) throw new Error('Failed to list tasks');
    return res.json();
  }

  async getTask(taskId: string): Promise<TaskState> {
    const res = await fetch(`${API_BASE}/tasks/${taskId}`);
    if (!res.ok) throw new Error(`Failed to load task ${taskId}`);
    return res.json();
  }

  async pauseTask(taskId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/tasks/${taskId}/pause`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to pause task');
    return res.json();
  }

  async resumeTask(taskId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/tasks/${taskId}/resume`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to resume task');
    return res.json();
  }

  async cancelTask(taskId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/tasks/${taskId}/cancel`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to cancel task');
    return res.json();
  }

  async getTaskEvents(taskId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/tasks/${taskId}/events`);
    if (!res.ok) throw new Error('Failed to load events');
    return res.json();
  }

  // --- Metrics ---
  async getMetrics(): Promise<MetricsSummary> {
    const res = await fetch(`${API_BASE}/metrics`);
    if (!res.ok) throw new Error('Failed to fetch metrics');
    return res.json();
  }

  // --- Memory ---
  async listExperiences(limit: number = 50): Promise<ExperienceEntry[]> {
    const res = await fetch(`${API_BASE}/memory?limit=${limit}`);
    if (!res.ok) throw new Error('Failed to list memory entries');
    return res.json();
  }

  async deleteExperience(entryId: number): Promise<any> {
    const res = await fetch(`${API_BASE}/memory/${entryId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete experience');
    return res.json();
  }

  async clearAllMemory(): Promise<any> {
    const res = await fetch(`${API_BASE}/memory`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to clear memory');
    return res.json();
  }

  async getAdvice(topic: string): Promise<{ recommended: any[]; avoid: any[] }> {
    const res = await fetch(`${API_BASE}/memory/advice?topic=${encodeURIComponent(topic)}`);
    if (!res.ok) throw new Error('Failed to fetch advice');
    return res.json();
  }

  // --- Knowledge Base ---
  async listDocuments(): Promise<KnowledgeDocument[]> {
    const res = await fetch(`${API_BASE}/knowledge`);
    if (!res.ok) throw new Error('Failed to list documents');
    return res.json();
  }

  async uploadDocument(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/knowledge/upload`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  }

  async deleteDocument(docId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/knowledge/${docId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete document');
    return res.json();
  }

  async searchKnowledge(query: string, topK: number = 5): Promise<{ query: string; count: number; results: KnowledgeSearchResult[] }> {
    const res = await fetch(`${API_BASE}/knowledge/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, top_k: topK })
    });
    if (!res.ok) throw new Error('Knowledge search failed');
    return res.json();
  }

  // --- Safety ---
  async getSafetyStatus(): Promise<SafetyStatus> {
    const res = await fetch(`${API_BASE}/safety`);
    if (!res.ok) throw new Error('Failed to load safety status');
    return res.json();
  }

  async getInterventions(): Promise<{ current_active: InterventionRequest | null; total_requests: number; history: InterventionRequest[] }> {
    const res = await fetch(`${API_BASE}/safety/interventions`);
    if (!res.ok) throw new Error('Failed to load interventions');
    return res.json();
  }

  async resolveIntervention(notes?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/safety/interventions/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notes: notes || 'Resolved by operator' })
    });
    if (!res.ok) throw new Error('Failed to resolve intervention');
    return res.json();
  }

  // --- WebSocket ---
  connectTaskWebSocket(taskId: string, onMessage: (data: any) => void, onError?: (err: any) => void): WebSocket {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/tasks/${taskId}/ws`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (e) {
        console.error('Failed to parse WS event', e);
      }
    };

    if (onError) {
      ws.onerror = onError;
    }

    return ws;
  }
}

export const api = new ApiService();
