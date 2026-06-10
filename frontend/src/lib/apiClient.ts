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

export interface ApiClient {
  baseUrl: string;
  fetchHealth: () => Promise<HealthResponse>;
  login: (email: string, password: string) => Promise<LoginResponse>;
  fetchMe: (accessToken?: string) => Promise<UserPublic>;
  logout: () => Promise<void>;
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
      throw new Error(`Request failed: ${response.status}`);
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
      throw new Error(`Request failed: ${response.status}`);
    }
    return response.json() as Promise<UserPublic>;
  }

  async function logout(): Promise<void> {
    await request<void>("/auth/logout", { method: "POST" });
  }

  return {
    baseUrl,
    fetchHealth,
    login,
    fetchMe,
    logout,
  };
}

export const apiClient = createApiClient();
