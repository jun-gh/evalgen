import { defineStore } from "pinia";
import { ref } from "vue";
import { evalService } from "@/services/evalService";
import { useUiStore } from "@/stores/uiStore";
import type { EvalSet, GenerationRequest } from "@/types";

export const useEvalStore = defineStore("evals", () => {
  const evalSets = ref<EvalSet[]>([]);
  const currentEvalSet = ref<EvalSet | null>(null);
  const activeModel = ref<string>(import.meta.env.VITE_GEMINI_MODEL || "gemini-3.8-flash");
  const isLoading = ref(false);
  const isGenerating = ref(false);
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

  return {
    evalSets,
    currentEvalSet,
    activeModel,
    isLoading,
    isGenerating,
    fetchConfig,
    loadEvalSets,
    loadEvalSet,
    generateEvals,
    deleteEvalSet,
  };
});
