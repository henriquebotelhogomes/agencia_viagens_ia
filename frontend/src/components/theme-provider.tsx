"use client";

import { useCallback } from "react";

/**
 * Mantido como compatibilidade caso algum componente ainda importe useTheme.
 */
export function useTheme() {
  const toggle = useCallback(() => {}, []);
  return { toggle };
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  return children;
}

