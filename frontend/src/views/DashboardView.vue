<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import { useEvalStore } from "@/stores/evalStore";
import { evalService } from "@/services/evalService";
import { Sparkles, Layers, FileDown, Trash2, ArrowRight, RefreshCw, Database, PlayCircle } from "lucide-vue-next";

const evalStore = useEvalStore();
const selectedDomain = ref<string>("All Domains");

const domains = [
  "All Domains",
  "Customer Support",
  "Coding",
  "Reasoning",
  "Healthcare",
  "Finance",
  "Tool Calling / MCP",
];

onMounted(() => {
  handleFilter();
});

function handleFilter() {
  const domain = selectedDomain.value === "All Domains" ? "" : selectedDomain.value;
  evalStore.loadEvalSets(domain);
}

async function handleExportCsv(es: { id: string; title: string }) {
  try {
    await evalService.downloadCsv(es.id, es.title);
  } catch (err) {
    console.error("Failed to export CSV:", err);
  }
}
</script>

<template>
  <div class="space-y-8">
    <!-- Hero / Action Banner -->
    <div class="rounded-2xl border border-slate-200 dark:border-slate-800 bg-gradient-to-br from-emerald-50/40 via-white to-slate-50 dark:from-slate-900 dark:via-slate-900 dark:to-emerald-950/30 p-5 sm:p-8 relative overflow-hidden shadow-sm">
      <div class="max-w-2xl">
        <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20 mb-3 font-mono">
          <Database class="w-3.5 h-3.5" />
          Zero-Cost Serverless Evals Generator
        </span>
        <h1 class="text-2xl sm:text-4xl font-bold tracking-tight text-slate-900 dark:text-white">
          AI Evaluation Sets
        </h1>
        <p class="mt-2 text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
          Design, synthesize, and benchmark rigorous evaluation test suites for LLM applications. Powered by Google Gemini ({{ evalStore.activeModel }}) with 3-attempt resilient backoff and MCP context tools.
        </p>

        <div class="mt-6 flex flex-col sm:flex-row flex-wrap gap-2.5 sm:gap-3">
          <RouterLink
            to="/generate"
            class="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl font-medium text-sm transition w-full sm:w-auto"
            :class="evalStore.isQuotaFull ? 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 border border-amber-500/30 hover:border-amber-500/60' : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-950/20 dark:shadow-emerald-950'"
          >
            <Sparkles class="w-4 h-4" :class="evalStore.isQuotaFull ? 'text-amber-500 dark:text-amber-400' : 'text-white'" />
            <span>Synthesize New Eval Set</span>
            <span v-if="evalStore.isQuotaFull" class="text-[11px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-700 dark:text-amber-300 font-mono">Quota Full</span>
          </RouterLink>

          <RouterLink
            to="/benchmark"
            class="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-medium text-sm border border-slate-300 dark:border-slate-700 shadow-sm transition w-full sm:w-auto"
          >
            <PlayCircle class="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            Run Benchmark Studio
          </RouterLink>

          <button
            @click="handleFilter()"
            class="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-medium text-sm border border-slate-300 dark:border-slate-700 shadow-sm transition w-full sm:w-auto"
          >
            <RefreshCw class="w-4 h-4 text-slate-500 dark:text-slate-400" :class="{ 'animate-spin': evalStore.isLoading }" />
            Refresh
          </button>
        </div>
      </div>
    </div>

    <!-- Quota Warning Banner if limit reached -->
    <div
      v-if="evalStore.isQuotaFull"
      class="rounded-xl border border-amber-200 dark:border-amber-500/30 bg-amber-50 dark:bg-amber-500/10 p-4 flex items-start gap-3 text-xs text-amber-900 dark:text-amber-200"
    >
      <Database class="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
      <div>
        <span class="font-semibold text-amber-950 dark:text-amber-300">Session Dataset Quota Full:</span>
        You have reached your limit of {{ evalStore.maxDatasets }} datasets for this anonymous session (lifespan: {{ evalStore.sessionExpiryDays }} days). To synthesize or import a new evaluation set, please delete an older one below.
      </div>
    </div>

    <!-- Filter & Statistics -->
    <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 sm:gap-4">
      <div class="flex items-center space-x-2">
        <label class="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wider font-semibold shrink-0">Filter:</label>
        <select
          v-model="selectedDomain"
          @change="handleFilter"
          class="flex-1 sm:flex-none bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:border-emerald-500 shadow-sm"
        >
          <option v-for="d in domains" :key="d" :value="d">{{ d }}</option>
        </select>
      </div>

      <div class="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
        <span class="w-full sm:w-auto inline-flex items-center justify-between sm:justify-start gap-1.5 px-3 py-1.5 sm:py-1 rounded-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 font-mono text-[11px] shadow-sm">
          <span>Session: <strong class="text-slate-900 dark:text-white">{{ evalStore.evalSets.length }} / {{ evalStore.maxDatasets }}</strong></span>
          <span class="text-slate-500">({{ evalStore.sessionExpiryDays }}d lifespan)</span>
        </span>
      </div>
    </div>

    <!-- Datasets Grid -->
    <div v-if="evalStore.isLoading && !evalStore.evalSets.length" class="text-center py-16">
      <RefreshCw class="w-8 h-8 text-emerald-600 dark:text-emerald-400 animate-spin mx-auto mb-3" />
      <p class="text-sm text-slate-500 dark:text-slate-400">Loading evaluation suites...</p>
    </div>

    <div v-else-if="!evalStore.evalSets.length" class="text-center py-16 border border-dashed border-slate-300 dark:border-slate-800 rounded-2xl p-8 bg-white/60 dark:bg-transparent">
      <Layers class="w-10 h-10 text-slate-400 dark:text-slate-600 mx-auto mb-3" />
      <h3 class="text-base font-semibold text-slate-800 dark:text-slate-300">No evaluation sets found</h3>
      <p class="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
        Get started by generating your first synthetic evaluation suite with Google Gemini ({{ evalStore.activeModel }}).
      </p>
      <RouterLink
        to="/generate"
        class="inline-flex items-center gap-2 mt-4 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs shadow-sm transition"
      >
        <Sparkles class="w-3.5 h-3.5" />
        Generate Eval Set
      </RouterLink>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      <div
        v-for="es in evalStore.evalSets"
        :key="es.id"
        class="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 hover:border-slate-300 dark:hover:border-slate-700 hover:shadow-md transition flex flex-col justify-between group overflow-hidden"
      >
        <div class="p-5">
          <div class="flex items-start justify-between gap-2 mb-2">
            <span class="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
              {{ es.domain }}
            </span>
            <span class="text-[11px] text-slate-400 dark:text-slate-500">
              {{ new Date(es.created_at).toLocaleDateString() }}
            </span>
          </div>

          <h3 class="text-base font-semibold text-slate-900 dark:text-white group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition line-clamp-1">
            {{ es.title }}
          </h3>
          <p class="text-xs text-slate-600 dark:text-slate-400 mt-1.5 line-clamp-2 leading-relaxed">
            {{ es.description || "No description provided." }}
          </p>

          <div class="mt-4 flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
            <span class="font-semibold text-slate-900 dark:text-white">{{ es.total_test_cases || es.test_cases?.length || 0 }}</span>
            test cases
            <span class="text-slate-300 dark:text-slate-700">•</span>
            <span class="capitalize text-slate-600 dark:text-slate-400">{{ es.eval_type }}</span>
          </div>
        </div>

        <div class="border-t border-slate-100 dark:border-slate-800/80 bg-slate-50/70 dark:bg-slate-950/40 px-5 py-3 flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <button
              type="button"
              @click="handleExportCsv(es)"
              class="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-200/60 dark:hover:bg-slate-800 transition"
              title="Download CSV export"
            >
              <FileDown class="w-4 h-4" />
            </button>
            <button
              @click="evalStore.deleteEvalSet(es.id)"
              class="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-slate-200/60 dark:hover:bg-slate-800 transition"
              title="Delete evaluation set"
            >
              <Trash2 class="w-4 h-4" />
            </button>
          </div>

          <div class="flex items-center gap-3">
            <RouterLink
              :to="`/benchmark?id=${es.id}`"
              class="text-xs font-semibold text-slate-500 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 flex items-center gap-1 transition"
              title="Run in-browser benchmark on this eval set"
            >
              <PlayCircle class="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              Benchmark
            </RouterLink>

            <RouterLink
              :to="`/evals/${es.id}`"
              class="text-xs font-semibold text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 flex items-center gap-1 transition"
            >
              Inspect
              <ArrowRight class="w-3.5 h-3.5" />
            </RouterLink>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
