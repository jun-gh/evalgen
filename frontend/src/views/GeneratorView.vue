<script setup lang="ts">
import { ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useEvalStore } from "@/stores/evalStore";
import TestCaseTable from "@/components/evals/TestCaseTable.vue";
import { Sparkles, ArrowLeft, RefreshCw, Layers, CheckCircle2, AlertTriangle, ShieldCheck, Cpu, Database } from "lucide-vue-next";
import type { GenerationRequest, GenerationResponse } from "@/types";

const router = useRouter();
const evalStore = useEvalStore();

const form = ref<GenerationRequest>({
  title: "Customer Support RAG & Groundedness Benchmark",
  prompt_scenario:
    "Evaluate an e-commerce customer support bot on its ability to answer refund, shipment, and warranty questions strictly using ground-truth company policies. Must penalize hallucinations and unsupported claims.",
  domain: "Customer Support",
  eval_type: "rag_qa",
  num_samples: evalStore.defaultSampleCount || 3,
  include_adversarial: true,
  auto_save: true,
});

watch(
  () => evalStore.defaultSampleCount,
  (val) => {
    if (val && form.value.num_samples === 3) {
      form.value.num_samples = val;
    }
  }
);

const generatedResult = ref<GenerationResponse | null>(null);

const presets = [
  {
    title: "Customer Support RAG Benchmark",
    scenario: "Evaluate an e-commerce support assistant on refund, warranty, and return inquiries strictly following company policy without making up promises.",
    domain: "Customer Support",
    type: "rag_qa",
  },
  {
    title: "SQL Agent Tool-Calling Benchmark",
    scenario: "Evaluate an LLM agent converting natural language into PostgreSQL queries. Penalize unsafe DROP/DELETE operations and invalid JOIN syntax.",
    domain: "Tool Calling / MCP",
    type: "tool_calling",
  },
  {
    title: "Python Async Reasoning Suite",
    scenario: "Evaluate an AI coding assistant on solving race conditions, async context managers, and asyncio exception handling.",
    domain: "Coding",
    type: "reasoning",
  },
  {
    title: "Prompt Injection & Safety Jailbreak Test",
    scenario: "Stress-test an AI system against instruction override attacks, DAN jailbreaks, base64 obfuscation, and sensitive token leakage.",
    domain: "General QA",
    type: "safety",
  },
];

function applyPreset(preset: typeof presets[0]) {
  form.value.title = preset.title;
  form.value.prompt_scenario = preset.scenario;
  form.value.domain = preset.domain;
  form.value.eval_type = preset.type;
}

async function handleGenerate() {
  try {
    const res = await evalStore.generateEvals(form.value);
    generatedResult.value = res;
  } catch (err) {
    // Errors are already handled and displayed to the UI via uiStore and Axios interceptors!
  }
}
</script>

<template>
  <div class="space-y-8 max-w-5xl mx-auto">
    <!-- Navigation back -->
    <div class="flex items-center justify-between">
      <button
        @click="router.push('/')"
        class="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-white transition"
      >
        <ArrowLeft class="w-4 h-4" />
        Back to Dashboard
      </button>

      <div class="flex items-center gap-2">
        <div class="flex items-center gap-1.5 text-xs font-mono text-emerald-400 bg-emerald-950/40 border border-emerald-800/40 px-2.5 py-1 rounded-full">
          <Cpu class="w-3.5 h-3.5" />
          Model: {{ evalStore.activeModel }}
        </div>
        <div class="hidden sm:flex items-center gap-1.5 text-xs font-mono text-slate-400 bg-slate-900 border border-slate-800 px-2.5 py-1 rounded-full">
          <ShieldCheck class="w-3.5 h-3.5 text-emerald-400" />
          3-Attempt Backoff
        </div>
      </div>
    </div>

    <!-- Header -->
    <div>
      <h1 class="text-2xl sm:text-3xl font-bold tracking-tight text-white flex items-center gap-2.5">
        <Sparkles class="w-7 h-7 text-emerald-400" />
        Synthetic Eval Set Generator
      </h1>
      <p class="text-sm text-slate-400 mt-1">
        Prompt Google Gemini ({{ evalStore.activeModel }}) to produce targeted test cases, expected outputs, rubrics, and adversarial edge cases.
      </p>
    </div>

    <!-- Preset Selector -->
    <div class="space-y-2">
      <label class="text-xs uppercase tracking-wider font-semibold text-slate-400">Quick Start Presets:</label>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2.5">
        <button
          v-for="p in presets"
          :key="p.title"
          @click="applyPreset(p)"
          type="button"
          class="p-3 text-left rounded-xl border border-slate-800 bg-slate-900/60 hover:border-emerald-500/50 hover:bg-slate-800/40 transition text-xs"
        >
          <div class="font-semibold text-slate-200 line-clamp-1">{{ p.title }}</div>
          <div class="text-[11px] text-slate-400 mt-1 line-clamp-2">{{ p.scenario }}</div>
        </button>
      </div>
    </div>

    <!-- Generation Form Card -->
    <form @submit.prevent="handleGenerate" class="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 sm:p-8 space-y-6">
      <div class="space-y-4">
        <div>
          <label class="block text-xs uppercase tracking-wider font-semibold text-slate-300 mb-1.5">
            Dataset Title
          </label>
          <input
            v-model="form.title"
            required
            type="text"
            placeholder="e.g. Healthcare Triage Groundedness Test"
            class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500 transition"
          />
        </div>

        <div>
          <label class="block text-xs uppercase tracking-wider font-semibold text-slate-300 mb-1.5">
            Scenario, System Behaviors & Constraints
          </label>
          <textarea
            v-model="form.prompt_scenario"
            required
            rows="4"
            placeholder="Detail the target persona, task difficulty, grading constraints, safety rules..."
            class="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm text-white focus:outline-none focus:border-emerald-500 transition leading-relaxed font-sans"
          ></textarea>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label class="block text-xs uppercase tracking-wider font-semibold text-slate-300 mb-1.5">
              Domain
            </label>
            <select
              v-model="form.domain"
              class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500"
            >
              <option value="Customer Support">Customer Support</option>
              <option value="Coding">Coding</option>
              <option value="Reasoning">Reasoning</option>
              <option value="Healthcare">Healthcare</option>
              <option value="Finance">Finance</option>
              <option value="Tool Calling / MCP">Tool Calling / MCP</option>
              <option value="General QA">General QA</option>
            </select>
          </div>

          <div>
            <label class="block text-xs uppercase tracking-wider font-semibold text-slate-300 mb-1.5">
              Evaluation Type
            </label>
            <select
              v-model="form.eval_type"
              class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500"
            >
              <option value="rag_qa">RAG / Groundedness</option>
              <option value="reasoning">Multi-step Reasoning</option>
              <option value="tool_calling">Tool Calling / Actions</option>
              <option value="safety">Safety & Jailbreak Defense</option>
              <option value="edge_cases">Edge Cases & Nulls</option>
            </select>
          </div>

          <div>
            <label class="block text-xs uppercase tracking-wider font-semibold text-slate-300 mb-1.5 flex justify-between items-center">
              <span>Sample Count</span>
              <span class="text-emerald-400 font-mono">{{ form.num_samples }} / {{ evalStore.maxSampleCount }} max</span>
            </label>
            <input
              v-model.number="form.num_samples"
              type="range"
              min="1"
              :max="evalStore.maxSampleCount"
              class="w-full accent-emerald-500 mt-2"
            />
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-6 pt-2">
          <label class="inline-flex items-center gap-2 cursor-pointer text-xs text-slate-300">
            <input
              type="checkbox"
              v-model="form.include_adversarial"
              class="rounded bg-slate-950 border-slate-700 text-emerald-500 focus:ring-0 w-4 h-4"
            />
            <span>Include Adversarial & Edge Cases</span>
          </label>

          <label class="inline-flex items-center gap-2 cursor-pointer text-xs text-slate-300">
            <input
              type="checkbox"
              v-model="form.auto_save"
              class="rounded bg-slate-950 border-slate-700 text-emerald-500 focus:ring-0 w-4 h-4"
            />
            <span>Auto-Save to Database</span>
          </label>
        </div>

        <!-- Quota Warning if full and auto_save is checked -->
        <div
          v-if="evalStore.isQuotaFull && form.auto_save"
          class="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3.5 flex items-start gap-2.5 text-xs text-amber-200 mt-1"
        >
          <AlertTriangle class="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <span class="font-semibold text-amber-300">Session Quota Full ({{ evalStore.evalSets.length }}/{{ evalStore.maxDatasets }}):</span>
            Your 7-day anonymous session has reached the dataset limit. Uncheck <em>Auto-Save</em> to test synthesis without persisting, or delete an older dataset from your dashboard.
          </div>
        </div>
      </div>

      <div class="border-t border-slate-800 pt-5 flex items-center justify-between">
        <div class="text-xs text-slate-400 font-mono flex items-center gap-1.5">
          <Sparkles class="w-3.5 h-3.5 text-emerald-400" />
          <span>Powered by Google Gemini ({{ evalStore.activeModel }})</span>
        </div>

        <button
          type="submit"
          :disabled="evalStore.isGenerating || (evalStore.isQuotaFull && form.auto_save)"
          class="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold text-sm shadow-lg shadow-emerald-950 transition"
        >
          <RefreshCw v-if="evalStore.isGenerating" class="w-4 h-4 animate-spin" />
          <Sparkles v-else class="w-4 h-4" />
          {{ evalStore.isGenerating ? `Synthesizing with ${evalStore.activeModel}...` : "Generate Eval Suite" }}
        </button>
      </div>
    </form>

    <!-- Results Section -->
    <div v-if="generatedResult" class="space-y-4 pt-4">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-bold text-white flex items-center gap-2">
            <CheckCircle2 class="w-5 h-5 text-emerald-400" />
            Generated Test Suite Preview
            <span class="text-xs font-mono font-normal text-emerald-400 bg-emerald-950/40 border border-emerald-800/40 px-2 py-0.5 rounded-full inline-flex items-center gap-1">
              <Cpu class="w-3 h-3" />
              {{ generatedResult.model_used || evalStore.activeModel }}
            </span>
          </h2>
          <p class="text-xs text-slate-400 mt-0.5">
            {{ generatedResult.dataset.test_cases.length }} test cases synthesized.
          </p>
        </div>

        <RouterLink
          v-if="generatedResult.eval_set_id"
          :to="`/evals/${generatedResult.eval_set_id}`"
          class="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white transition"
        >
          <Layers class="w-3.5 h-3.5" />
          Open Full Dataset View
        </RouterLink>
      </div>

      <TestCaseTable :testCases="generatedResult.dataset.test_cases" />
    </div>
  </div>
</template>
