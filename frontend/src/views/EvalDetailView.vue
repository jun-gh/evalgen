<script setup lang="ts">
import { onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useEvalStore } from "@/stores/evalStore";
import { evalService } from "@/services/evalService";
import TestCaseTable from "@/components/evals/TestCaseTable.vue";
import { ArrowLeft, FileDown, Trash2, RefreshCw, Layers, Cpu, PlayCircle } from "lucide-vue-next";

const route = useRoute();
const router = useRouter();
const evalStore = useEvalStore();

const evalSetId = route.params.id as string;

onMounted(() => {
  evalStore.loadEvalSet(evalSetId);
});

async function handleExportCsv() {
  try {
    const title = evalStore.currentEvalSet?.title || evalSetId;
    await evalService.downloadCsv(evalSetId, title);
  } catch (err) {
    console.error("Failed to export CSV:", err);
  }
}

async function handleDelete() {
  if (confirm("Are you sure you want to delete this evaluation dataset?")) {
    await evalStore.deleteEvalSet(evalSetId);
    router.push("/");
  }
}
</script>

<template>
  <div class="space-y-6 max-w-6xl mx-auto">
    <!-- Back button -->
    <div>
      <button
        @click="router.push('/')"
        class="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white transition"
      >
        <ArrowLeft class="w-4 h-4" />
        Back to All Datasets
      </button>
    </div>

    <!-- Loading -->
    <div v-if="evalStore.isLoading && !evalStore.currentEvalSet" class="text-center py-20">
      <RefreshCw class="w-8 h-8 text-emerald-600 dark:text-emerald-400 animate-spin mx-auto mb-3" />
      <p class="text-sm text-slate-500 dark:text-slate-400">Loading dataset details...</p>
    </div>

    <div v-else-if="evalStore.currentEvalSet" class="space-y-6">
      <!-- Header Banner -->
      <div class="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-5 sm:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-sm">
        <div class="space-y-2">
          <div class="flex flex-wrap items-center gap-2">
            <span class="text-xs font-mono px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20">
              {{ evalStore.currentEvalSet.domain }}
            </span>
            <span class="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              {{ evalStore.currentEvalSet.eval_type }}
            </span>
            <span class="text-xs font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 inline-flex items-center gap-1">
              <Cpu class="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
              Target Model: {{ evalStore.activeModel }}
            </span>
          </div>

          <h1 class="text-xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            {{ evalStore.currentEvalSet.title }}
          </h1>

          <p class="text-xs sm:text-sm text-slate-600 dark:text-slate-400 max-w-2xl leading-relaxed">
            {{ evalStore.currentEvalSet.description || "No description provided." }}
          </p>

          <div class="text-xs text-slate-500 dark:text-slate-400 pt-1">
            Created: {{ new Date(evalStore.currentEvalSet.created_at).toLocaleString() }}
          </div>
        </div>

        <div class="flex flex-col sm:flex-row flex-wrap items-stretch sm:items-center gap-2.5 sm:gap-3 w-full md:w-auto">
          <RouterLink
            :to="`/benchmark?id=${evalSetId}`"
            class="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs shadow-md shadow-emerald-600/20 dark:shadow-emerald-950 transition"
          >
            <PlayCircle class="w-4 h-4" />
            Run Benchmark
          </RouterLink>

          <button
            type="button"
            @click="handleExportCsv"
            class="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-medium text-xs border border-slate-300 dark:border-slate-700 transition"
          >
            <FileDown class="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            Export CSV
          </button>

          <button
            @click="handleDelete"
            class="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-rose-50 hover:bg-rose-100 dark:bg-rose-950/40 dark:hover:bg-rose-900/60 text-rose-700 dark:text-rose-300 font-medium text-xs border border-rose-200 dark:border-rose-800/40 transition"
          >
            <Trash2 class="w-4 h-4" />
            Delete
          </button>
        </div>
      </div>

      <!-- Test Cases Table -->
      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <h2 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Layers class="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            Test Cases ({{ evalStore.currentEvalSet.test_cases?.length || 0 }})
          </h2>
        </div>

        <TestCaseTable
          v-if="evalStore.currentEvalSet.test_cases?.length"
          :testCases="evalStore.currentEvalSet.test_cases"
        />

        <div v-else class="text-center py-12 border border-dashed border-slate-300 dark:border-slate-800 rounded-xl p-6 text-slate-500 dark:text-slate-400 text-sm">
          No test cases registered for this dataset.
        </div>
      </div>
    </div>
  </div>
</template>
