import { defineStore } from "pinia";
import { ref } from "vue";
import { evalService } from "@/services/evalService";
import { useUiStore } from "@/stores/uiStore";
import type { EvalSet, GenerationRequest, EvalRun, BenchmarkRunRequest } from "@/types";

export const useEvalStore = defineStore("evals", () => {
  const evalSets = ref<EvalSet[]>([]);
  const currentEvalSet = ref<EvalSet | null>(null);
  const currentRun = ref<EvalRun | null>(null);
  const activeModel = ref<string>(import.meta.env.VITE_GEMINI_MODEL || "gemini-3.8-flash");
  const isLoading = ref(false);
  const isGenerating = ref(false);
  const isBenchmarking = ref(false);
  const uiStore = useUiStore();

  async function fetchConfig() {
    try {
      const cfg = await evalService.getConfig();
      if (cfg && cfg.gemini_model) {
        activeModel.value = cfg.gemini_model;
      }
    } catch (err) {
      console.warn("Could not fetch remote config, using default/env model:", activeModel.value);
    }
  }

  // Trigger initial config fetch
  fetchConfig();

  async function loadEvalSets() {
    isLoading.value = true;
    try {
      evalSets.value = await evalService.listEvalSets();
    } catch (err: any) {
      console.error("Failed to load eval sets:", err);
    } finally {
      isLoading.value = false;
    }
  }

  async function loadEvalSet(id: string) {
    isLoading.value = true;
    try {
      currentEvalSet.value = await evalService.getEvalSet(id);
    } catch (err: any) {
      console.error(`Failed to load eval set ${id}:`, err);
    } finally {
      isLoading.value = false;
    }
  }

  async function generateEvals(request: GenerationRequest) {
    isGenerating.value = true;
    try {
      const response = await evalService.generateEvalSet(request);
      uiStore.addToast({
        type: "success",
        title: "Evals Generated!",
        message: `Successfully synthesized ${response.dataset.test_cases.length} evaluation test cases.`,
      });

      if (response.eval_set_id) {
        await loadEvalSets();
      }
      return response;
    } catch (err: any) {
      console.error("Generation error:", err);
      throw err;
    } finally {
      isGenerating.value = false;
    }
  }

  async function deleteEvalSet(id: string) {
    try {
      await evalService.deleteEvalSet(id);
      evalSets.value = evalSets.value.filter((es) => es.id !== id);
      if (currentEvalSet.value?.id === id) {
        currentEvalSet.value = null;
      }
      uiStore.addToast({
        type: "success",
        title: "Deleted",
        message: "Evaluation set deleted successfully.",
      });
    } catch (err: any) {
      console.error("Failed to delete eval set:", err);
    }
  }

  async function importCsv(file: File): Promise<EvalSet> {
    isLoading.value = true;
    try {
      const created = await evalService.importCsv(file);
      uiStore.addToast({
        type: "success",
        title: "CSV Imported!",
        message: `Successfully imported "${created.title}" with ${created.total_test_cases || created.test_cases?.length || 0} test cases.`,
      });
      await loadEvalSets();
      currentEvalSet.value = created;
      return created;
    } catch (err: any) {
      console.error("Failed to import CSV:", err);
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  async function runBenchmark(evalSetId: string, payload?: BenchmarkRunRequest): Promise<EvalRun> {
    isBenchmarking.value = true;
    try {
      const run = await evalService.runBenchmark(evalSetId, payload);
      currentRun.value = run;
      uiStore.addToast({
        type: "success",
        title: "Benchmark Complete!",
        message: `Scored ${run.total_count} test cases: ${run.accuracy_rate}% pass rate.`,
      });
      return run;
    } catch (err: any) {
      console.error("Benchmark run failed:", err);
      throw err;
    } finally {
      isBenchmarking.value = false;
    }
  }

  return {
    evalSets,
    currentEvalSet,
    currentRun,
    activeModel,
    isLoading,
    isGenerating,
    isBenchmarking,
    fetchConfig,
    loadEvalSets,
    loadEvalSet,
    generateEvals,
    deleteEvalSet,
    importCsv,
    runBenchmark,
  };
});
