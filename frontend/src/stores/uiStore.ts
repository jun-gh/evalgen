import { defineStore } from "pinia";
import { ref } from "vue";
import type { ErrorDetail } from "@/types";

export interface ToastItem {
  id: string;
  type: "error" | "warning" | "success" | "info";
  title: string;
  message: string;
  trace_id?: string;
  retryable?: boolean;
  onRetry?: () => void;
}

export const useUiStore = defineStore("ui", () => {
  const toasts = ref<ToastItem[]>([]);
  const isServerWakingUp = ref(false);
  const serverStatus = ref<"online" | "waking" | "offline">("waking");

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

  function showError(error: ErrorDetail | { message: string; code?: string; trace_id?: string }, onRetry?: () => void) {
    return addToast({
      type: "error",
      title: error.code ? `Error: ${error.code}` : "Request Failed",
      message: error.message || "An unexpected error occurred",
      trace_id: error.trace_id,
      retryable: "retryable" in error ? error.retryable : !!onRetry,
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
    addToast,
    showError,
    removeToast,
    setServerStatus,
  };
});
