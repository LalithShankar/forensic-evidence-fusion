import { ChakraProvider, defaultSystem } from "@chakra-ui/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, type RenderOptions } from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";
import { MemoryRouter, type MemoryRouterProps } from "react-router-dom";

import {
  AuthProvider,
  type AuthProviderProps,
} from "../context/AuthContext";

interface ProviderOptions {
  routerProps?: MemoryRouterProps;
  authProps?: Omit<AuthProviderProps, "children">;
}

export function renderWithProviders(
  ui: ReactElement,
  {
    routerProps,
    authProps,
    ...renderOptions
  }: ProviderOptions & RenderOptions = {},
) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  function Wrapper({ children }: { children: ReactNode }) {
    return (
      <ChakraProvider value={defaultSystem}>
        <QueryClientProvider client={queryClient}>
          <MemoryRouter {...routerProps}>
            <AuthProvider {...authProps}>{children}</AuthProvider>
          </MemoryRouter>
        </QueryClientProvider>
      </ChakraProvider>
    );
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions });
}
