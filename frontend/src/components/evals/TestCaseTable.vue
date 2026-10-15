<script setup lang="ts">
import { ref } from "vue";
import type { TestCase } from "@/types";
import { ChevronDown, ChevronRight, ShieldAlert, Sparkles, CheckSquare } from "lucide-vue-next";

defineProps<{
  testCases: TestCase[];
}>();

const expandedRows = ref<Set<number>>(new Set([0]));

function toggleRow(index: number) {
  if (expandedRows.value.has(index)) {
    expandedRows.value.delete(index);
  } else {
    expandedRows.value.add(index);
  }
}

function getDifficultyBadge(diff: string) {
  switch (diff?.toLowerCase()) {
    case "easy":
      return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
    case "medium":
      return "bg-blue-500/10 text-blue-400 border-blue-500/20";
    case "hard":
      return "bg-amber-500/10 text-amber-400 border-amber-500/20";
    case "adversarial":
      return "bg-purple-500/10 text-purple-400 border-purple-500/20";
    default:
      return "bg-slate-800 text-slate-300 border-slate-700";
  }
}
</script>

<template>
  <div class="border border-slate-800 rounded-xl overflow-hidden bg-slate-900/50">
    <div class="overflow-x-auto">
      <table class="w-full text-left text-sm">
        <thead class="bg-slate-900 text-slate-400 text-xs uppercase tracking-wider border-b border-slate-800">
          <tr>
            <th class="py-3 px-4 w-12 text-center">#</th>
            <th class="py-3 px-4 w-2/5">Prompt Input</th>
            <th class="py-3 px-4 w-2/5">Expected Output</th>
            <th class="py-3 px-4 text-center">Difficulty</th>
            <th class="py-3 px-4 text-right">Details</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-800 font-normal">
          <template v-for="(tc, index) in testCases" :key="tc.id || index">
            <tr
              @click="toggleRow(index)"
              class="hover:bg-slate-800/40 cursor-pointer transition select-none"
              :class="{ 'bg-slate-800/20': expandedRows.has(index) }"
            >
              <td class="py-3.5 px-4 text-center font-mono text-xs text-slate-500">
                {{ index + 1 }}
              </td>

              <td class="py-3.5 px-4">
                <div class="line-clamp-2 text-slate-200 font-medium leading-relaxed">
                  {{ tc.prompt_input }}
                </div>
                <div v-if="tc.tags?.length" class="flex flex-wrap gap-1 mt-1.5">
                  <span
                    v-for="tag in tc.tags"
                    :key="tag"
                    class="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 font-mono"
                  >
                    #{{ tag }}
                  </span>
                </div>
              </td>

              <td class="py-3.5 px-4">
                <div class="line-clamp-2 text-slate-400 leading-relaxed">
                  {{ tc.expected_output }}
                </div>
              </td>

              <td class="py-3.5 px-4 text-center">
                <span
                  class="text-xs px-2 py-0.5 rounded-full border font-medium uppercase tracking-wider"
                  :class="getDifficultyBadge(tc.difficulty)"
                >
                  {{ tc.difficulty }}
                </span>
              </td>

              <td class="py-3.5 px-4 text-right">
                <button class="p-1 rounded hover:bg-slate-700 text-slate-400 hover:text-white transition">
                  <ChevronDown v-if="expandedRows.has(index)" class="w-4 h-4" />
                  <ChevronRight v-else class="w-4 h-4" />
                </button>
              </td>
            </tr>

            <!-- Expanded Row details: Rubric, Context & Assertions -->
            <tr v-if="expandedRows.has(index)" class="bg-slate-950/60">
              <td colspan="5" class="p-5 border-t border-slate-800">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div class="space-y-3">
                    <div>
                      <div class="flex items-center gap-1.5 font-semibold text-emerald-400 mb-1">
                        <Sparkles class="w-3.5 h-3.5" />
                        Grading Rubric
                      </div>
                      <div class="p-3 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 font-mono whitespace-pre-wrap leading-relaxed">
                        {{ tc.rubric || "No explicit rubric specified." }}
                      </div>
                    </div>

                    <div v-if="tc.context">
                      <div class="font-semibold text-slate-400 mb-1">Context / Reference Snippet</div>
                      <div class="p-3 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 font-mono text-[11px] max-h-36 overflow-y-auto">
                        {{ tc.context }}
                      </div>
                    </div>
                  </div>

                  <div class="space-y-3">
                    <div>
                      <div class="flex items-center gap-1.5 font-semibold text-blue-400 mb-1">
                        <CheckSquare class="w-3.5 h-3.5" />
                        Full Golden Answer
                      </div>
                      <div class="p-3 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 whitespace-pre-wrap leading-relaxed">
                        {{ tc.expected_output }}
                      </div>
                    </div>

                    <div v-if="tc.assertions?.length">
                      <div class="font-semibold text-purple-400 mb-1">Validation Assertions</div>
                      <div class="p-2.5 rounded-lg bg-slate-900 border border-slate-800 space-y-1 font-mono text-[11px]">
                        <div v-for="(ass, aIdx) in tc.assertions" :key="aIdx" class="text-slate-300">
                          - <span class="text-purple-400">{{ ass.type }}</span>: {{ ass.value || ass.rubric }}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</template>
