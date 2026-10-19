import { apiClient } from "./api";
import type { EvalSet, GenerationRequest, GenerationResponse, AppConfig, EvalRun, BenchmarkRunRequest } from "@/types";

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
        max_datasets_per_session: healthRes.data.max_datasets_per_session || 5,
        session_expiry_days: healthRes.data.session_expiry_days || 7,
        max_sample_count: healthRes.data.max_sample_count || 10,
        default_sample_count: healthRes.data.default_sample_count || 3,
      };
    }
  },

  async listEvalSets(domain?: string, limit = 100): Promise<EvalSet[]> {
    const params: Record<string, any> = { limit };
    if (domain) params.domain = domain;
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
    const res = await apiClient.post<GenerationResponse>("/generator/generate", payload, {
      timeout: 120000, // 2 minutes for LLM synthetic generation
    });
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

  async importCsv(file: File): Promise<EvalSet> {
    const formData = new FormData();
    formData.append("file", file);
    const res = await apiClient.post<EvalSet>("/eval-sets/import-csv", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return res.data;
  },

  async runBenchmark(evalSetId: string, payload?: BenchmarkRunRequest): Promise<EvalRun> {
    const res = await apiClient.post<EvalRun>(`/eval-sets/${evalSetId}/run`, payload || {}, {
      timeout: 180000, // 3 minutes for multi-testcase LLM generation and judge grading
    });
    return res.data;
  },

  async listEvalRuns(evalSetId: string): Promise<EvalRun[]> {
    const res = await apiClient.get<EvalRun[]>(`/eval-sets/${evalSetId}/runs`);
    return res.data;
  },

  async getEvalRun(runId: string): Promise<EvalRun> {
    const res = await apiClient.get<EvalRun>(`/eval-sets/runs/${runId}`);
    return res.data;
  },
};
