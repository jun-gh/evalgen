import { apiClient } from "./api";
import type { EvalSet, GenerationRequest, GenerationResponse } from "@/types";

export const evalService = {
  async getHealth() {
    const res = await apiClient.get("/health");
    return res.data;
  },

  async listEvalSets(domain?: string): Promise<EvalSet[]> {
    const params = domain ? { domain } : {};
    const res = await apiClient.get<EvalSet[]>("/eval-sets", { params });
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
