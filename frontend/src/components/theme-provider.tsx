"use client";

import { useCallback } from "react";

const STORAGE_KEY = "voyager-theme";

/**
 * Alterna entre tema claro e escuro.
 *
 * Deliberadamente **sem estado no React**: o script inline do `layout.tsx` já
 * aplica a classe `dark` no `<html>` antes da primeira pintura, e o CSS decide
 * o que mostrar. Guardar o tema em `useState` exigiria sincronizar com o DOM
 * dentro de um `useEffect` — o que causa render em cascata e um descompasso de
 * hidratação (o servidor não sabe a preferência do usuário).
 */
export function useTheme() {
  const toggle = useCallback(() => {
    const isDark = document.documentElement.classList.toggle("dark");
    localStorage.setItem(STORAGE_KEY, isDark ? "dark" : "light");
  }, []);

  return { toggle };
}

/**
 * Mantido como componente para não espalhar a decisão pelo layout: se um dia o
 * tema precisar de contexto (ex.: mais de dois temas), a mudança fica aqui.
 */
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  return children;
}
