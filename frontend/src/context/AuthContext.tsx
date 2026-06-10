import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useNavigate } from "react-router-dom";

import {
  createApiClient,
  configureApiClientAuth,
  type ApiClient,
  type UserPublic,
} from "../lib/apiClient";

export interface AuthContextValue {
  user: UserPublic | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  client: ApiClient;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export interface AuthProviderProps {
  children: ReactNode;
  initialToken?: string | null;
  initialUser?: UserPublic | null;
}

export function AuthProvider({
  children,
  initialToken = null,
  initialUser = null,
}: AuthProviderProps) {
  const navigate = useNavigate();
  const [token, setToken] = useState<string | null>(initialToken);
  const [user, setUser] = useState<UserPublic | null>(initialUser);
  const [isLoading, setIsLoading] = useState(false);
  const client = useMemo(() => createApiClient(), []);

  const clearAuth = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    configureApiClientAuth(
      () => token,
      () => {
        clearAuth();
        navigate("/login", { replace: true });
      },
    );
  }, [token, clearAuth, navigate]);

  const login = useCallback(
    async (email: string, password: string) => {
      setIsLoading(true);
      try {
        const response = await client.login(email, password);
        const profile = await client.fetchMe(response.access_token);
        setToken(response.access_token);
        setUser(profile);
      } finally {
        setIsLoading(false);
      }
    },
    [client],
  );

  const logout = useCallback(async () => {
    if (token) {
      try {
        await client.logout();
      } catch {
        // Stateless JWT logout is best-effort on the client.
      }
    }
    clearAuth();
    navigate("/login", { replace: true });
  }, [clearAuth, client, navigate, token]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(token && user),
      isLoading,
      login,
      logout,
      client,
    }),
    [client, isLoading, login, logout, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
