<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import { useEvalStore } from "@/stores/evalStore";
import { evalService } from "@/services/evalService";
import { Sparkles, Layers, FileDown, Trash2, ArrowRight, RefreshCw, Database } from "lucide-vue-next";

const evalStore = useEvalStore();
const selectedDomain = ref<string>("");

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
  evalStore.loadEvalSets();
});

function handleFilter() {
  const domain = selectedDomain.value === "All Domains" ? "" : selectedDomain.value;
  evalStore.loadEvalSets();
}

function getDownloadUrl(id: string) {
  return evalService.getExportCsvUrl(id);
}
</script>

<template>
  <div class="space-y-8">
    <!-- Hero / Action Banner -->
    <div class="rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900 via-slate-900 to-emerald-950/30 p-6 sm:p-8 relative overflow-hidden">
      <div class="max-w-2xl">
        <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 mb-3 font-mono">
          <Database class="w-3.5 h-3.5" />
          Zero-Cost Serverless Evals Generator
        </span>
        <h1 class="text-3xl font-bold tracking-tight text-white sm:text-4xl">
          AI Evaluation Sets
        </h1>
        <p class="mt-2 text-sm text-slate-400 leading-relaxed">
          Design, synthesize, and benchmark rigorous evaluation test suites for LLM applications. Powered by Google Gemini with 3-attempt resilient backoff and MCP context tools.
        </p>

        <div class="mt-6 flex flex-wrap gap-3">
          <RouterLink
            to="/generate"
            class="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-sm shadow-lg shadow-emerald-950 transition"
          >
            <Sparkles class="w-4 h-4" />
            Synthesize New Eval Set
          </RouterLink>

          <button
            @click="evalStore.loadEvalSets()"
            class="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-sm border border-slate-700 transition"
          >
            <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': evalStore.isLoading }" />
            Refresh
          </button>
        </div>
      </div>
    </div>

    <!-- Filter & Statistics -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      <div class="flex items-center space-x-2">
        <label class="text-xs text-slate-400 uppercase tracking-wider font-semibold">Filter:</label>
        <select
          v-model="selectedDomain"
          @change="handleFilter"
          class="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
        >
          <option v-for="d in domains" :key="d" :value="d">{{ d }}</option>
        </select>
      </div>

      <div class="text-xs text-slate-400">
        Total Datasets: <span class="font-bold text-white">{{ evalStore.evalSets.length }}</span>
      </div>
    </div>

    <!-- Datasets Grid -->
    <div v-if="evalStore.isLoading && !evalStore.evalSets.length" class="text-center py-16">
      <RefreshCw class="w-8 h-8 text-emerald-400 animate-spin mx-auto mb-3" />
      <p class="text-sm text-slate-400">Loading evaluation suites...</p>
    </div>

    <div v-else-if="!evalStore.evalSets.length" class="text-center py-16 border border-dashed border-slate-800 rounded-2xl p-8">
      <Layers class="w-10 h-10 text-slate-600 mx-auto mb-3" />
      <h3 class="text-base font-semibold text-slate-300">No evaluation sets found</h3>
      <p class="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
        Get started by generating your first synthetic evaluation suite with Google Gemini.
      </p>
      <RouterLink
        to="/generate"
        class="inline-flex items-center gap-2 mt-4 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs transition"
      >
        <Sparkles class="w-3.5 h-3.5" />
        Generate Eval Set
      </RouterLink>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      <div
        v-for="es in evalStore.evalSets"
        :key="es.id"
        class="rounded-xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 transition flex flex-col justify-between group overflow-hidden"
      >
        <div class="p-5">
          <div class="flex items-start justify-between gap-2 mb-2">
            <span class="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
              {{ es.domain }}
            </span>
            <span class="text-[11px] text-slate-500">
              {{ new Date(es.created_at).toLocaleDateString() }}
            </span>
          </div>

          <h3 class="text-base font-semibold text-white group-hover:text-emerald-400 transition line-clamp-1">
            {{ es.title }}
          </h3>
          <p class="text-xs text-slate-400 mt-1.5 line-clamp-2 leading-relaxed">
            {{ es.description || "No description provided." }}
          </p>

          <div class="mt-4 flex items-center gap-2 text-xs text-slate-400">
            <span class="font-semibold text-white">{{ es.total_test_cases || es.test_cases?.length || 0 }}</span>
            test cases
            <span class="text-slate-700">•</span>
            <span class="capitalize text-slate-400">{{ es.eval_type }}</span>
          </div>
        </div>

        <div class="border-t border-slate-800/80 bg-slate-950/40 px-5 py-3 flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <a
              :href="getDownloadUrl(es.id)"
              download
              class="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              title="Download CSV export"
            >
              <FileDown class="w-4 h-4" />
            </a>
            <button
              @click="evalStore.deleteEvalSet(es.id)"
              class="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition"
              title="Delete evaluation set"
            >
              <Trash2 class="w-4 h-4" />
            </button>
          </div>

          <RouterLink
            :to="`/evals/${es.id}`"
            class="text-xs font-semibold text-emerald-400 hover:text-emerald-300 flex items-center gap-1 transition"
          >
            Inspect Evals
            <ArrowRight class="w-3.5 h-3.5" />
          </RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>
