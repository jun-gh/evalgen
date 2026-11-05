import { defineStore } from "pinia";
import { ref } from "vue";
import type { ErrorDetail } from "@/types";

export interface ToastItem {
  id: string;
  type: "error" | "warning" | "success" | "info";
  title: string;
  message: string;
  code?: string;
  trace_id?: string;
  retryable?: boolean;
  retry_count?: number;
  onRetry?: () => void;
}

export const useUiStore = defineStore("ui", () => {
  const toasts = ref<ToastItem[]>([]);
  const isServerWakingUp = ref(false);
  const serverStatus = ref<"online" | "waking" | "offline">("waking");

  // Theme management: default to dark (matching initial app theme) or saved preference
  const theme = ref<"dark" | "light">("dark");

  function initTheme() {
    if (typeof window === "undefined") return;
    try {
      const stored = localStorage.getItem("evalgen_theme");
      const current = stored === "light" ? "light" : "dark";
      applyTheme(current, false);
    } catch {
      applyTheme("dark", false);
    }

    // Keep tabs synchronized
    window.addEventListener("storage", (e) => {
      if (e.key === "evalgen_theme" && (e.newValue === "light" || e.newValue === "dark")) {
        applyTheme(e.newValue, false);
      }
    });
  }

  function applyTheme(newTheme: "dark" | "light", persist = true) {
    theme.value = newTheme;
    if (persist) {
      try {
        localStorage.setItem("evalgen_theme", newTheme);
      } catch {}
    }
    if (typeof document !== "undefined") {
      if (newTheme === "dark") {
        document.documentElement.classList.add("dark");
      } else {
        document.documentElement.classList.remove("dark");
      }
      const meta = document.querySelector('meta[name="color-scheme"]');
      if (meta) {
        meta.setAttribute("content", newTheme);
      }
    }
  }

  function toggleTheme() {
    const next = theme.value === "dark" ? "light" : "dark";
    applyTheme(next, true);
  }

  // Initialize theme on store creation
  initTheme();

  function addToast(toast: Omit<ToastItem, "id">) {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
    const newToast: ToastItem = { ...toast, id };
    toasts.value.push(newToast);

    // Auto-dismiss success/info toasts after 5 seconds
    if (toast.type === "success" || toast.type === "info") {
      setTimeout(() => {
        removeToast(id);
      }, 5000);
    }
    return id;
  }

  function showError(
    error: ErrorDetail | { message: string; code?: string; trace_id?: string; retryable?: boolean; retry_count?: number },
    onRetry?: () => void
  ) {
    return addToast({
      type: "error",
      title: error.code ? `Error: ${error.code}` : "Request Failed",
      message: error.message || "An unexpected error occurred",
      code: error.code,
      trace_id: error.trace_id,
      retryable: "retryable" in error ? error.retryable : !!onRetry,
      retry_count: "retry_count" in error ? error.retry_count : 0,
      onRetry,
    });
  }

  function removeToast(id: string) {
    toasts.value = toasts.value.filter((t) => t.id !== id);
  }

  function setServerStatus(status: "online" | "waking" | "offline") {
    serverStatus.value = status;
    isServerWakingUp.value = status === "waking";
  }

  return {
    toasts,
    isServerWakingUp,
    serverStatus,
    theme,
    toggleTheme,
    applyTheme,
    addToast,
    showError,
    removeToast,
    setServerStatus,
  };
});
