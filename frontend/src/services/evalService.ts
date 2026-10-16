import { apiClient } from "./api";
import type { EvalSet, GenerationRequest, GenerationResponse, AppConfig } from "@/types";

export const evalService = {
  async getHealth() {
    const res = await apiClient.get("/health");
    return res.data;
  },

  async getConfig(): Promise<AppConfig> {
    try {
      const res = await apiClient.get<AppConfig>("/config");
      return res.data;
    } catch {
      // Fallback to /health which also contains gemini_model
      const healthRes = await apiClient.get("/health");
      return {
        app_name: healthRes.data.app || "EvalGen",
        environment: healthRes.data.environment || "production",
        gemini_model: healthRes.data.gemini_model || "gemini-3.8-flash",
        gemini_configured: Boolean(healthRes.data.gemini_configured),
      };
    }
  },

  async listEvalSets(domain?: string): Promise<EvalSet[]> {
    const params = domain ? { domain } : {};
    const res = await apiClient.get<EvalSet[]>("/eval-sets", { params });
    if (!Array.isArray(res.data)) {
      console.warn("[evalService] Expected array from /eval-sets, got:", typeof res.data);
      return [];
    }
    return res.data;
  },

  async getEvalSet(id: string): Promise<EvalSet> {
    const res = await apiClient.get<EvalSet>(`/eval-sets/${id}`);
    return res.data;
  },

  async deleteEvalSet(id: string): Promise<void> {
    await apiClient.delete(`/eval-sets/${id}`);
  },

  async generateEvalSet(payload: GenerationRequest): Promise<GenerationResponse> {
    const res = await apiClient.post<GenerationResponse>("/generator/generate", payload);
    return res.data;
  },

  async listMcpTools(): Promise<any[]> {
    const res = await apiClient.get("/mcp-tools");
    return res.data;
  },

  getExportCsvUrl(id: string): string {
    const base = apiClient.defaults.baseURL || "/api/v1";
    return `${base}/eval-sets/${id}/export/csv`;
  },
};
