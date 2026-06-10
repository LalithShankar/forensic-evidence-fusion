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
  source_group?: string | null;
  created_at: string;
  updated_at: string;
}

export interface TimelineEventFilters {
  event_type?: string;
  source_group?: string;
  review_status?: string;
}

export interface ClaimCreateInput {
  claim_text: string;
  claimant?: string | null;
  claimed_time_text?: string | null;
  claimed_people?: string[] | null;
  claim_source?: string | null;
}

export interface ClaimPublic {
  id: string;
  case_id: string;
  claim_text: string;
  claim_type: string;
  claimant: string | null;
  claimed_time_text: string | null;
  claimed_time_normalized: string | null;
  claimed_people: string[] | null;
  claim_source: string | null;
  claim_source_artifact_id: string | null;
  parse_confidence: number;
  created_by: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ClaimResolutionPublic {
  id: string;
  case_id: string;
  claim_id: string;
  resolution_status: string;
  result_label: string | null;
  support_score: number | null;
  contradiction_score: number | null;
  supporting_event_ids: string[] | null;
  contradicting_event_ids: string[] | null;
  unresolved_reason: string | null;
  resolution_notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface SourceReferencePublic {
  chunk_id: string;
  artifact_id: string;
  event_id: string | null;
  provenance_pointer: string | null;
  source_group: string | null;
}

export interface AssistantAnswerPublic {
  answer_text: string;
  confidence: number;
  limitation_text: string | null;
  insufficient_evidence: boolean;
  source_references: SourceReferencePublic[];
  log_id: string;
}

export interface ReportSectionPublic {
  key: string;
  title: string;
  content: Record<string, unknown>;
}

export interface ReportDraftPublic {
  id: string;
  case_id: string;
  title: string;
  status: string;
  content_json: {
    version: number;
    generated_at: string;
    summary: string;
    sections: ReportSectionPublic[];
  } | null;
  created_at: string;
  updated_at: string;
}

export interface GenerateReportInput {
  title?: string | null;
}

export interface AuditLogPublic {
  audit_id: string;
  case_id: string | null;
  user_id: string;
  action: string;
  object_type: string;
  object_id: string;
  before_json: Record<string, unknown> | null;
  after_json: Record<string, unknown> | null;
  timestamp: string;
  reason: string | null;
}

export interface AuditLogListResponse {
  items: AuditLogPublic[];
  total: number;
  limit: number;
  offset: number;
}

export interface AuditLogFilters {
  action?: string;
  object_type?: string;
  since?: string;
  until?: string;
  limit?: number;
  offset?: number;
}

export interface OperationsSummaryPublic {
  cases_count: number;
  artifacts: {
    failed: number;
    blocked: number;
    needs_review: number;
    other: number;
  };
  transformations: {
    running: number;
    failed: number;
    blocked: number;
    completed: number;
  };
  search_chunks: {
    failed: number;
    pending: number;
    indexed: number;
  };
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
  listTimelineEvents: (
    caseId: string,
    filters?: TimelineEventFilters,
  ) => Promise<EvidenceEventPublic[]>;
  getTimelineEvent: (
    caseId: string,
    eventId: string,
  ) => Promise<EvidenceEventPublic>;
  createClaim: (caseId: string, input: ClaimCreateInput) => Promise<ClaimPublic>;
  listClaims: (caseId: string) => Promise<ClaimPublic[]>;
  getClaim: (caseId: string, claimId: string) => Promise<ClaimPublic>;
  resolveClaim: (
    caseId: string,
    claimId: string,
  ) => Promise<ClaimResolutionPublic>;
  getClaimResolution: (
    caseId: string,
    claimId: string,
  ) => Promise<ClaimResolutionPublic>;
  askAssistant: (
    caseId: string,
    question: string,
  ) => Promise<AssistantAnswerPublic>;
  generateReport: (
    caseId: string,
    input?: GenerateReportInput,
  ) => Promise<ReportDraftPublic>;
  listReports: (caseId: string) => Promise<ReportDraftPublic[]>;
  getReport: (caseId: string, reportId: string) => Promise<ReportDraftPublic>;
  listAuditLogs: (
    caseId: string,
    filters?: AuditLogFilters,
  ) => Promise<AuditLogListResponse>;
  getOperationsSummary: () => Promise<OperationsSummaryPublic>;
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
    return listTimelineEvents(caseId);
  }

  async function listTimelineEvents(
    caseId: string,
    filters: TimelineEventFilters = {},
  ): Promise<EvidenceEventPublic[]> {
    const params = new URLSearchParams();
    if (filters.event_type) {
      params.set("event_type", filters.event_type);
    }
    if (filters.source_group) {
      params.set("source_group", filters.source_group);
    }
    if (filters.review_status) {
      params.set("review_status", filters.review_status);
    }
    const query = params.toString();
    const suffix = query ? `?${query}` : "";
    return request<EvidenceEventPublic[]>(`/cases/${caseId}/events${suffix}`);
  }

  async function getTimelineEvent(
    caseId: string,
    eventId: string,
  ): Promise<EvidenceEventPublic> {
    return request<EvidenceEventPublic>(
      `/cases/${caseId}/events/${eventId}`,
    );
  }

  async function createClaim(
    caseId: string,
    input: ClaimCreateInput,
  ): Promise<ClaimPublic> {
    return request<ClaimPublic>(`/cases/${caseId}/claims`, {
      method: "POST",
      body: JSON.stringify(input),
    });
  }

  async function listClaims(caseId: string): Promise<ClaimPublic[]> {
    return request<ClaimPublic[]>(`/cases/${caseId}/claims`);
  }

  async function getClaim(
    caseId: string,
    claimId: string,
  ): Promise<ClaimPublic> {
    return request<ClaimPublic>(`/cases/${caseId}/claims/${claimId}`);
  }

  async function resolveClaim(
    caseId: string,
    claimId: string,
  ): Promise<ClaimResolutionPublic> {
    return request<ClaimResolutionPublic>(
      `/cases/${caseId}/claims/${claimId}/resolve`,
      { method: "POST" },
    );
  }

  async function getClaimResolution(
    caseId: string,
    claimId: string,
  ): Promise<ClaimResolutionPublic> {
    return request<ClaimResolutionPublic>(
      `/cases/${caseId}/claims/${claimId}/resolution`,
    );
  }

  async function askAssistant(
    caseId: string,
    question: string,
  ): Promise<AssistantAnswerPublic> {
    return request<AssistantAnswerPublic>(`/cases/${caseId}/assistant/ask`, {
      method: "POST",
      body: JSON.stringify({ question }),
    });
  }

  async function generateReport(
    caseId: string,
    input: GenerateReportInput = {},
  ): Promise<ReportDraftPublic> {
    return request<ReportDraftPublic>(`/cases/${caseId}/reports/generate`, {
      method: "POST",
      body: JSON.stringify(input),
    });
  }

  async function listReports(caseId: string): Promise<ReportDraftPublic[]> {
    return request<ReportDraftPublic[]>(`/cases/${caseId}/reports`);
  }

  async function getReport(
    caseId: string,
    reportId: string,
  ): Promise<ReportDraftPublic> {
    return request<ReportDraftPublic>(
      `/cases/${caseId}/reports/${reportId}`,
    );
  }

  async function listAuditLogs(
    caseId: string,
    filters: AuditLogFilters = {},
  ): Promise<AuditLogListResponse> {
    const params = new URLSearchParams();
    if (filters.action) {
      params.set("action", filters.action);
    }
    if (filters.object_type) {
      params.set("object_type", filters.object_type);
    }
    if (filters.since) {
      params.set("since", filters.since);
    }
    if (filters.until) {
      params.set("until", filters.until);
    }
    if (filters.limit !== undefined) {
      params.set("limit", String(filters.limit));
    }
    if (filters.offset !== undefined) {
      params.set("offset", String(filters.offset));
    }
    const query = params.toString();
    const suffix = query ? `?${query}` : "";
    return request<AuditLogListResponse>(`/cases/${caseId}/audit${suffix}`);
  }

  async function getOperationsSummary(): Promise<OperationsSummaryPublic> {
    return request<OperationsSummaryPublic>("/operations/summary");
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
    listTimelineEvents,
    getTimelineEvent,
    createClaim,
    listClaims,
    getClaim,
    resolveClaim,
    getClaimResolution,
    askAssistant,
    generateReport,
    listReports,
    getReport,
    listAuditLogs,
    getOperationsSummary,
  };
}

export const apiClient = createApiClient();
