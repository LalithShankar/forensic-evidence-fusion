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
  };
}

export const apiClient = createApiClient();
