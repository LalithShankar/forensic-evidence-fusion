export interface AppConfig {
  appEnv: "local" | "deployed";
  apiBaseUrl: string;
}

export function loadConfig(): AppConfig {
  const appEnv = import.meta.env.VITE_APP_ENV === "deployed" ? "deployed" : "local";
  const apiBaseUrl =
    import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

  return { appEnv, apiBaseUrl };
}
