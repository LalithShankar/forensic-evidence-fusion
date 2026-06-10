import { loadConfig, type AppConfig } from "../config";

export interface HealthResponse {
  status: string;
  app_env: string;
  secrets_source: string;
}

export interface UserPublic {
  id: string;
  email: string;
  display_name: string;
  role: "analyst" | "case_manager" | "admin";
  status: "active" | "disabled";
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export type CaseScenarioType =
  | "general_investigation"
  | "financial_fraud"
  | "insider_trading"
  | "money_laundering";

export interface CasePublic {
  id: string;
  name: string;
  description: string | null;
  scenario_type: CaseScenarioType;
  date_range_start: string | null;
  date_range_end: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface CaseCreateInput {
  name: string;
  description?: string | null;
  scenario_type: CaseScenarioType;
  date_range_start?: string | null;
  date_range_end?: string | null;
}

export interface CaseUpdateInput {
  name?: string;
  description?: string | null;
  scenario_type?: CaseScenarioType;
  date_range_start?: string | null;
  date_range_end?: string | null;
}

export type ArtifactStatus =
  | "pending"
  | "preserved"
  | "failed"
  | "blocked"
  | "needs_review"
  | "ready_for_transformation"
  | "preserve_only";

export interface ArtifactMetadataInput {
  source_group?: string;
  source_family?: string;
  artifact_type?: string;
  collection_method?: string;
  parser_class?: string;
  provenance_notes?: string;
}

export interface ArtifactPublic {
  id: string;
  case_id: string;
  original_filename: string;
  file_size_bytes: number;
  file_extension: string;
  mime_type: string;
  uploaded_by: string | null;
  uploaded_at: string | null;
  content_hash: string | null;
  status: ArtifactStatus;
  source_group: string;
  source_family: string;
  artifact_type: string;
  collection_method: string;
  parser_class: string;
  provenance_notes: string | null;
  upload_batch_id: string | null;
  classification_confidence: number | null;
  suggested_source_group: string;
  suggested_source_family: string;
  suggested_artifact_type: string;
  classification_reason: string | null;
  blocker_notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface BulkUploadItemPublic {
  filename: string;
  artifact: ArtifactPublic | null;
  error: string | null;
}

export interface BulkUploadResponse {
  upload_batch_id: string;
  results: BulkUploadItemPublic[];
  succeeded_count: number;
  failed_count: number;
}

export interface ReviewQueueItem {
  artifact: ArtifactPublic;
  review_reason: string;
  suggested_category: string;
}

export interface ReviewQueueResponse {
  items: ReviewQueueItem[];
  total: number;
}

export interface ReviewActionInput {
  source_group?: string;
  source_family?: string;
  artifact_type?: string;
  action: "approve" | "preserve_only" | "correct";
}

export interface ReviewActionResponse {
  artifact: ArtifactPublic;
  message: string;
}

export type ReadableViewType = "extracted_text" | "inventory";
export type ReadableViewStatus = "generated" | "partial" | "failed";

export interface ReadableViewPublic {
  id: string;
  artifact_id: string;
  transformation_id: string | null;
  view_type: ReadableViewType;
  storage_path: string | null;
  status: ReadableViewStatus;
  error_notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReadableViewContentPublic {
  view_id: string;
  view_type: ReadableViewType;
  content_type: string;
  content: string;
  truncated: boolean;
}

export type StructuredDatasetStatus = "generated" | "failed";

export interface StructuredDatasetPublic {
  id: string;
  artifact_id: string;
  transformation_id: string | null;
  dataset_type: string;
  storage_path: string | null;
  row_count: number | null;
  schema_version: string;
  confidence: number;
  status: StructuredDatasetStatus;
  error_notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface StructuredDatasetPreviewPublic {
  dataset_id: string;
  dataset_type: string;
  confidence: number;
  row_count: number | null;
  preview_rows: Record<string, string>[] | null;
  preview_json: string | null;
  truncated: boolean;
  total_rows: number | null;
}

export type ReviewStatus = "pending" | "reviewed" | "disputed";

export interface EvidenceEventPublic {
  id: string;
  case_id: string;
  artifact_id: string;
  transformation_id: string | null;
  structured_dataset_id: string | null;
  event_type: string;
  event_subtype: string | null;
  original_timestamp_text: string | null;
  normalized_timestamp: string | null;
  title: string | null;
  description: string | null;
  payload_json: Record<string, unknown> | null;
  source_confidence: number;
  provenance_pointer: string | null;
  review_status: ReviewStatus;
  created_at: string;
  updated_at: string;
}

export interface ValidationErrorDetail {
  loc: (string | number)[];
  msg: string;
  type: string;
}

export class ApiRequestError extends Error {
  status: number;
  detail: string | ValidationErrorDetail[];

  constructor(status: number, detail: string | ValidationErrorDetail[]) {
    super(`Request failed: ${status}`);
    this.name = "ApiRequestError";
    this.status = status;
    this.detail = detail;
  }
}

export interface ApiClient {
  baseUrl: string;
  fetchHealth: () => Promise<HealthResponse>;
  login: (email: string, password: string) => Promise<LoginResponse>;
  fetchMe: (accessToken?: string) => Promise<UserPublic>;
  logout: () => Promise<void>;
  listCases: () => Promise<CasePublic[]>;
  createCase: (input: CaseCreateInput) => Promise<CasePublic>;
  getCase: (caseId: string) => Promise<CasePublic>;
  updateCase: (caseId: string, input: CaseUpdateInput) => Promise<CasePublic>;
  listArtifacts: (caseId: string) => Promise<ArtifactPublic[]>;
  getArtifact: (caseId: string, artifactId: string) => Promise<ArtifactPublic>;
  uploadArtifact: (
    caseId: string,
    file: File,
    metadata?: ArtifactMetadataInput,
  ) => Promise<ArtifactPublic>;
  bulkUploadArtifacts: (
    caseId: string,
    files: File[],
  ) => Promise<BulkUploadResponse>;
  getReviewQueue: (caseId: string) => Promise<ReviewQueueResponse>;
  reviewArtifact: (
    caseId: string,
    artifactId: string,
    input: ReviewActionInput,
  ) => Promise<ReviewActionResponse>;
  listReadableViews: (
    caseId: string,
    artifactId: string,
  ) => Promise<ReadableViewPublic[]>;
  fetchReadableContent: (
    caseId: string,
    artifactId: string,
    viewId: string,
  ) => Promise<ReadableViewContentPublic>;
  listStructuredDatasets: (
    caseId: string,
    artifactId: string,
  ) => Promise<StructuredDatasetPublic[]>;
  fetchStructuredDatasetPreview: (
    caseId: string,
    artifactId: string,
    datasetId: string,
  ) => Promise<StructuredDatasetPreviewPublic>;
  listCaseEvents: (caseId: string) => Promise<EvidenceEventPublic[]>;
}

type TokenProvider = () => string | null;
type UnauthorizedHandler = () => void;

let tokenProvider: TokenProvider = () => null;
let unauthorizedHandler: UnauthorizedHandler | undefined;

export function configureApiClientAuth(
  getToken: TokenProvider,
  onUnauthorized?: UnauthorizedHandler,
): void {
  tokenProvider = getToken;
  unauthorizedHandler = onUnauthorized;
}

export function formatValidationErrors(
  detail: string | ValidationErrorDetail[],
): string {
  if (typeof detail === "string") {
    return detail;
  }
  return detail
    .map((entry) => {
      const field = entry.loc[entry.loc.length - 1];
      return `${String(field)}: ${entry.msg}`;
    })
    .join("; ");
}

export function createApiClient(config: AppConfig = loadConfig()): ApiClient {
  const baseUrl = config.apiBaseUrl.replace(/\/$/, "");

  async function request<T>(
    path: string,
    init: RequestInit = {},
  ): Promise<T> {
    const headers = new Headers(init.headers);
    const token = tokenProvider();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    if (init.body && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }

    const response = await fetch(`${baseUrl}${path}`, {
      ...init,
      headers,
    });

    if (response.status === 401 && token) {
      unauthorizedHandler?.();
    }

    if (!response.ok) {
      let detail: string | ValidationErrorDetail[] = `Request failed: ${response.status}`;
      try {
        const body = (await response.json()) as {
          detail?: string | ValidationErrorDetail[];
        };
        if (body.detail !== undefined) {
          detail = body.detail;
        }
      } catch {
        // Keep generic detail when the body is not JSON.
      }
      throw new ApiRequestError(response.status, detail);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json() as Promise<T>;
  }

  async function fetchHealth(): Promise<HealthResponse> {
    return request<HealthResponse>("/health");
  }

  async function login(email: string, password: string): Promise<LoginResponse> {
    return request<LoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  async function fetchMe(accessToken?: string): Promise<UserPublic> {
    const headers = new Headers();
    const token = accessToken ?? tokenProvider();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    const response = await fetch(`${baseUrl}/auth/me`, { headers });
    if (response.status === 401 && token) {
      unauthorizedHandler?.();
    }
    if (!response.ok) {
      throw new ApiRequestError(response.status, "Request failed");
    }
    return response.json() as Promise<UserPublic>;
  }

  async function logout(): Promise<void> {
    await request<void>("/auth/logout", { method: "POST" });
  }

  async function listCases(): Promise<CasePublic[]> {
    return request<CasePublic[]>("/cases");
  }

  async function createCase(input: CaseCreateInput): Promise<CasePublic> {
    return request<CasePublic>("/cases", {
      method: "POST",
      body: JSON.stringify(input),
    });
  }

  async function getCase(caseId: string): Promise<CasePublic> {
    return request<CasePublic>(`/cases/${caseId}`);
  }

  async function updateCase(
    caseId: string,
    input: CaseUpdateInput,
  ): Promise<CasePublic> {
    return request<CasePublic>(`/cases/${caseId}`, {
      method: "PATCH",
      body: JSON.stringify(input),
    });
  }

  async function listArtifacts(caseId: string): Promise<ArtifactPublic[]> {
    return request<ArtifactPublic[]>(`/cases/${caseId}/artifacts`);
  }

  async function getArtifact(
    caseId: string,
    artifactId: string,
  ): Promise<ArtifactPublic> {
    return request<ArtifactPublic>(
      `/cases/${caseId}/artifacts/${artifactId}`,
    );
  }

  async function uploadArtifact(
    caseId: string,
    file: File,
    metadata: ArtifactMetadataInput = {},
  ): Promise<ArtifactPublic> {
    const formData = new FormData();
    formData.append("file", file);
    if (metadata.source_group) {
      formData.append("source_group", metadata.source_group);
    }
    if (metadata.source_family) {
      formData.append("source_family", metadata.source_family);
    }
    if (metadata.artifact_type) {
      formData.append("artifact_type", metadata.artifact_type);
    }
    if (metadata.collection_method) {
      formData.append("collection_method", metadata.collection_method);
    }
    if (metadata.parser_class) {
      formData.append("parser_class", metadata.parser_class);
    }
    if (metadata.provenance_notes) {
      formData.append("provenance_notes", metadata.provenance_notes);
    }

    const headers = new Headers();
    const token = tokenProvider();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    const response = await fetch(
      `${baseUrl}/cases/${caseId}/artifacts/upload`,
      {
        method: "POST",
        headers,
        body: formData,
      },
    );

    if (response.status === 401 && token) {
      unauthorizedHandler?.();
    }

    if (!response.ok) {
      let detail: string | ValidationErrorDetail[] =
        `Request failed: ${response.status}`;
      try {
        const body = (await response.json()) as {
          detail?: string | ValidationErrorDetail[];
        };
        if (body.detail !== undefined) {
          detail = body.detail;
        }
      } catch {
        // Keep generic detail when the body is not JSON.
      }
      throw new ApiRequestError(response.status, detail);
    }

    return response.json() as Promise<ArtifactPublic>;
  }

  async function bulkUploadArtifacts(
    caseId: string,
    files: File[],
  ): Promise<BulkUploadResponse> {
    const formData = new FormData();
    for (const file of files) {
      formData.append("files", file);
    }

    const headers = new Headers();
    const token = tokenProvider();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    const response = await fetch(
      `${baseUrl}/cases/${caseId}/artifacts/bulk-upload`,
      {
        method: "POST",
        headers,
        body: formData,
      },
    );

    if (response.status === 401 && token) {
      unauthorizedHandler?.();
    }

    if (!response.ok) {
      let detail: string | ValidationErrorDetail[] =
        `Request failed: ${response.status}`;
      try {
        const body = (await response.json()) as {
          detail?: string | ValidationErrorDetail[];
        };
        if (body.detail !== undefined) {
          detail = body.detail;
        }
      } catch {
        // Keep generic detail when the body is not JSON.
      }
      throw new ApiRequestError(response.status, detail);
    }

    return response.json() as Promise<BulkUploadResponse>;
  }

  async function getReviewQueue(caseId: string): Promise<ReviewQueueResponse> {
    return request<ReviewQueueResponse>(`/cases/${caseId}/review-queue`);
  }

  async function reviewArtifact(
    caseId: string,
    artifactId: string,
    input: ReviewActionInput,
  ): Promise<ReviewActionResponse> {
    return request<ReviewActionResponse>(
      `/cases/${caseId}/review-queue/${artifactId}`,
      {
        method: "PATCH",
        body: JSON.stringify(input),
      },
    );
  }

  async function listReadableViews(
    caseId: string,
    artifactId: string,
  ): Promise<ReadableViewPublic[]> {
    return request<ReadableViewPublic[]>(
      `/cases/${caseId}/artifacts/${artifactId}/readable-views`,
    );
  }

  async function fetchReadableContent(
    caseId: string,
    artifactId: string,
    viewId: string,
  ): Promise<ReadableViewContentPublic> {
    return request<ReadableViewContentPublic>(
      `/cases/${caseId}/artifacts/${artifactId}/readable-views/${viewId}/content`,
    );
  }

  async function listStructuredDatasets(
    caseId: string,
    artifactId: string,
  ): Promise<StructuredDatasetPublic[]> {
    return request<StructuredDatasetPublic[]>(
      `/cases/${caseId}/artifacts/${artifactId}/structured-datasets`,
    );
  }

  async function fetchStructuredDatasetPreview(
    caseId: string,
    artifactId: string,
    datasetId: string,
  ): Promise<StructuredDatasetPreviewPublic> {
    return request<StructuredDatasetPreviewPublic>(
      `/cases/${caseId}/artifacts/${artifactId}/structured-datasets/${datasetId}/preview`,
    );
  }

  async function listCaseEvents(caseId: string): Promise<EvidenceEventPublic[]> {
    return request<EvidenceEventPublic[]>(`/cases/${caseId}/events`);
  }

  return {
    baseUrl,
    fetchHealth,
    login,
    fetchMe,
    logout,
    listCases,
    createCase,
    getCase,
    updateCase,
    listArtifacts,
    getArtifact,
    uploadArtifact,
    bulkUploadArtifacts,
    getReviewQueue,
    reviewArtifact,
    listReadableViews,
    fetchReadableContent,
    listStructuredDatasets,
    fetchStructuredDatasetPreview,
    listCaseEvents,
  };
}

export const apiClient = createApiClient();
