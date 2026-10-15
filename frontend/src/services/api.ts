import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { useUiStore } from "@/stores/uiStore";
import type { ErrorEnvelope } from "@/types";

const API_BASE_URL = import.meta.env.VITE_API_URL || "/api/v1";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 45000, // 45 seconds to accommodate LLM synthetic generation
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor: Attach client trace ID
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (!config.headers["X-Trace-ID"]) {
    config.headers["X-Trace-ID"] = `client-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;
  }
  return config;
});

// Custom retry config interface
interface CustomAxiosRequestConfig extends InternalAxiosRequestConfig {
  _retryCount?: number;
}

const MAX_CLIENT_RETRIES = 3;

// Response interceptor: Automated 3-attempt retry for idempotent requests & global error notification
apiClient.interceptors.response.use(
  (response) => {
    // If the server returned HTML instead of JSON (happens when VITE_API_URL is missing and SPA router returns index.html)
    const contentType = String(response.headers["content-type"] || "");
    if (
      typeof response.data === "string" &&
      (contentType.includes("text/html") || response.data.trim().startsWith("<!doctype") || response.data.trim().startsWith("<html"))
    ) {
      const uiStore = useUiStore();
      const err = {
        code: "BACKEND_NOT_CONFIGURED",
        message:
          "Frontend received HTML instead of API data. Please set VITE_API_URL in Cloudflare Pages settings to your Render backend URL (e.g. https://evalgen-backend.onrender.com/api/v1).",
        trace_id: "client-config",
        retryable: false,
        retry_count: 0,
        timestamp: new Date().toISOString(),
      };
      uiStore.showError(err);
      return Promise.reject(err);
    }

    // If the server responded with valid data, mark server status as online
    const uiStore = useUiStore();
    if (uiStore.serverStatus !== "online") {
      uiStore.setServerStatus("online");
    }
    return response;
  },
  async (error: AxiosError<any>) => {
    const config = error.config as CustomAxiosRequestConfig;
    const uiStore = useUiStore();

    // Check if error is due to cold start / network unreachable
    if (!error.response && error.code === "ERR_NETWORK") {
      uiStore.setServerStatus("waking");
    }

    // Only retry safe, idempotent methods (GET, HEAD, OPTIONS) on client side
    // Non-idempotent operations (POST generation) are already retried up to 3x on the backend
    const isSafeMethod = config?.method?.toLowerCase() === "get";
    const isNetworkError = !error.response;
    const isRetryableStatus = error.response && [502, 503, 504].includes(error.response.status);

    if (config && isSafeMethod && (isRetryableStatus || isNetworkError)) {
      config._retryCount = config._retryCount || 0;

      if (config._retryCount < MAX_CLIENT_RETRIES) {
        config._retryCount += 1;
        const delayMs = Math.pow(2, config._retryCount) * 1000 + Math.random() * 500;
        console.warn(
          `[EvalGen API] Retrying request (Attempt ${config._retryCount}/${MAX_CLIENT_RETRIES}) in ${Math.round(delayMs)}ms...`
        );
        await new Promise((resolve) => setTimeout(resolve, delayMs));
        return apiClient(config);
      }
    }

    // Surface formatted error to UI
    let errorDetail = {
      code: "NETWORK_ERROR",
      message: "Unable to reach the EvalGen server. Please ensure the backend is running at http://localhost:8000.",
      trace_id: (config?.headers?.["X-Trace-ID"] as string) || "unknown",
      retryable: true,
      retry_count: config?._retryCount || 0,
      timestamp: new Date().toISOString(),
    };

    if (error.response?.data?.error) {
      errorDetail = error.response.data.error;
    } else if (error.response?.data?.detail) {
      errorDetail.message =
        typeof error.response.data.detail === "string"
          ? error.response.data.detail
          : JSON.stringify(error.response.data.detail);
      errorDetail.code = `HTTP_${error.response.status}`;
    }

    uiStore.showError(errorDetail);
    return Promise.reject(errorDetail);
  }
);
