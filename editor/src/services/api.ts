export type ApiError = {
  code: string;
  message: string;
  details?: { field: string; message: string }[] | null;
};

export type ApiEnvelope<T> = {
  data: T | null;
  error: ApiError | null;
  meta?: Record<string, unknown> | null;
};

export class EditorApiError extends Error {
  status: number;
  body: ApiError | null;

  constructor(status: number, body: ApiError | null, fallback: string) {
    super(body?.message || fallback);
    this.status = status;
    this.body = body;
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (init?.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(path, { ...init, headers });
  let payload: ApiEnvelope<T>;
  try {
    payload = (await response.json()) as ApiEnvelope<T>;
  } catch {
    throw new EditorApiError(response.status, null, "后端无响应，请先启动 FastAPI");
  }
  if (!response.ok || payload.error || payload.data === null || payload.data === undefined) {
    throw new EditorApiError(response.status, payload.error, response.statusText);
  }
  return payload.data;
}

export type Project = {
  id: string;
  code: string;
  name: string;
  description: string | null;
  schema_version: string;
  content_version: number;
  target_start_year: number | null;
  target_end_year: number | null;
};

export type CharacterSummary = {
  id: string;
  code: string;
  name: string;
  courtesy_name: string | null;
  gender: string;
  birth_year: number | null;
  death_year: number | null;
  identity: string | null;
};

export type ValidationIssue = {
  rule: string;
  severity: string;
  message: string;
  entity_type: string;
  entity_id: string | null;
};

export type ValidationReport = {
  mode: string;
  valid: boolean;
  error_count: number;
  warning_count: number;
  issues: ValidationIssue[];
};

export type Health = {
  status: string;
  schema_version: string;
  api_version: string;
};

export const listProjects = () => api<Project[]>("/api/v1/projects");
export const createProject = (name: string) =>
  api<Project>("/api/v1/projects", { method: "POST", body: JSON.stringify({ name }) });
export const getProject = (projectId: string) => api<Project>(`/api/v1/projects/${projectId}`);
export const listCharacters = (projectId: string) =>
  api<CharacterSummary[]>(`/api/v1/projects/${projectId}/characters`);
export const createCharacter = (projectId: string, payload: unknown) =>
  api<unknown>(`/api/v1/projects/${projectId}/characters`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
export const validateProject = (projectId: string) =>
  api<ValidationReport>(`/api/v1/projects/${projectId}/validation`);
export const exportProject = (projectId: string) =>
  api<{ export_dir: string; package: { manifest: { schema_version: string; content_version: number } } }>(
    `/api/v1/projects/${projectId}/export`,
    { method: "POST" },
  );
export const getHealth = () => api<Health>("/health");
