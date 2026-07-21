import { HealthResponse, HybridConfig, RouteRequest, RouteResponse, RouterInfo } from '../types/router';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/health`, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.statusText}`);
  }
  return res.json();
}

export async function getRouters(): Promise<RouterInfo[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/router/routers`, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`Failed to fetch routers: ${res.statusText}`);
  }
  return res.json();
}

export async function routeQuestion(payload: RouteRequest): Promise<RouteResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/router/route`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const detail = err.detail;
    throw new Error(typeof detail === 'object' ? (detail.message || detail.code || 'Routing failed') : (detail || `Routing failed: ${res.statusText}`));
  }
  return res.json();
}

export async function compareRouters(payload: { question: string; history: string[]; router_ids?: string[]; hybrid_config?: HybridConfig }): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/v1/router/compare`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const detail = err.detail;
    throw new Error(typeof detail === 'object' ? (detail.message || detail.code || 'Compare failed') : (detail || `Compare failed: ${res.statusText}`));
  }
  return res.json();
}

export async function runEvaluation(router_ids: string[], dataset_id?: string, limit?: number, hybrid_config?: HybridConfig) {
  const payload: any = { router_ids };
  if (dataset_id) payload.dataset_id = dataset_id;
  if (limit) payload.limit = limit;
  if (hybrid_config) payload.hybrid_config = hybrid_config;
  const res = await fetch(`${API_BASE_URL}/api/v1/evaluations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Evaluation failed: ${res.statusText}`);
  }
  return res.json();
}

export async function getEvaluationErrors(run_id: string) {
  const res = await fetch(`${API_BASE_URL}/api/v1/evaluations/${run_id}/errors`);
  if (!res.ok) throw new Error('Failed to fetch errors');
  return res.json();
}

export async function getEvaluationAnalysis(run_id: string) {
  const res = await fetch(`${API_BASE_URL}/api/v1/evaluations/${run_id}/analysis`);
  if (!res.ok) throw new Error('Failed to fetch analysis');
  return res.json();
}

export async function listDatasets() {
  const res = await fetch(`${API_BASE_URL}/api/v1/datasets`);
  if (!res.ok) throw new Error('Failed to list datasets');
  return res.json();
}

export async function uploadDataset(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  
  const res = await fetch(`${API_BASE_URL}/api/v1/datasets/upload`, {
    method: 'POST',
    body: formData,
  });
  
  const data = await res.json();
  if (!res.ok) {
    if (data.detail) {
      throw new Error(JSON.stringify(data.detail));
    }
    throw new Error('Upload failed');
  }
  return data;
}

export async function getQwenServiceUrl(): Promise<{ url: string }> {
  const res = await fetch(`${API_BASE_URL}/api/v1/settings/qwen-service`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch Qwen Service URL');
  return res.json();
}

export interface QwenServiceStatus {
  configured: boolean;
  connection_status: 'not_configured' | 'not_tested' | 'connected' | 'stale' | 'model_not_loaded' | 'unreachable';
  model_loaded?: boolean | null;
  model_name?: string | null;
  device?: string | null;
  startup_error?: string | null;
  checked_at?: string | null;
  service_version?: string | null;
}

export async function getQwenServiceStatus(): Promise<QwenServiceStatus> {
  const res = await fetch(`${API_BASE_URL}/api/v1/settings/qwen-service/status`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch Qwen Service status');
  return res.json();
}

export async function setQwenServiceUrl(url: string): Promise<{ status: string, url: string }> {
  const res = await fetch(`${API_BASE_URL}/api/v1/settings/qwen-service`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  });
  if (!res.ok) throw new Error('Failed to save Qwen Service URL');
  return res.json();
}

export async function testQwenServiceConnection(): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/v1/settings/qwen-service/test`, {
    method: 'POST',
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || 'Test connection failed');
  }
  return data;
}

export interface OpenRouterStatus {
  configured: boolean;
  source: 'runtime' | 'environment' | null;
  connection_status: string;
  error_code: string | null;
  error_message: string | null;
  last_checked_at: string | null;
}

export async function getOpenRouterStatus(): Promise<OpenRouterStatus> {
  const res = await fetch(`${API_BASE_URL}/api/v1/settings/openrouter/status`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch OpenRouter status');
  return res.json();
}

async function postOpenRouterKey(path: string, api_key: string): Promise<OpenRouterStatus> {
  const res = await fetch(`${API_BASE_URL}/api/v1/settings/openrouter${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail?.message || data.detail || 'OpenRouter request failed');
  return data;
}

export function verifyOpenRouterKey(api_key: string): Promise<OpenRouterStatus> {
  return postOpenRouterKey('/verify', api_key);
}

export function setOpenRouterKey(api_key: string): Promise<OpenRouterStatus> {
  return postOpenRouterKey('', api_key);
}

export async function deleteOpenRouterRuntimeKey(): Promise<OpenRouterStatus> {
  const res = await fetch(`${API_BASE_URL}/api/v1/settings/openrouter`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete runtime OpenRouter key');
  return res.json();
}
