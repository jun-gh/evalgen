<script setup lang="ts">
import { useUiStore } from "@/stores/uiStore";
import { Server, RefreshCw } from "lucide-vue-next";

const uiStore = useUiStore();
</script>

<template>
  <div
    v-if="uiStore.isServerWakingUp"
    class="bg-amber-50 dark:bg-amber-500/10 border-b border-amber-200 dark:border-amber-500/30 text-amber-900 dark:text-amber-200 px-4 py-2.5 text-xs sm:text-sm transition"
  >
    <div class="max-w-7xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2.5 w-full">
      <div class="flex items-start sm:items-center gap-2.5 flex-1">
        <div class="p-1 rounded bg-amber-100 dark:bg-amber-500/20 text-amber-700 dark:text-amber-400 animate-pulse shrink-0 mt-0.5 sm:mt-0">
          <Server class="w-4 h-4" />
        </div>
        <div class="flex-1 leading-snug">
          <span class="font-semibold text-amber-950 dark:text-amber-300">Waking up backend service:</span>
          <span class="ml-1 text-amber-900/90 dark:text-amber-200/90">
            Render's zero-cost tier scales to zero when idle. Your first request is waking the server up (~30-45s) and will auto-complete.
          </span>
        </div>
      </div>
      <div class="flex items-center gap-1.5 text-xs text-amber-700 dark:text-amber-400 font-mono self-end sm:self-center shrink-0">
        <RefreshCw class="w-3.5 h-3.5 animate-spin" />
        <span>Connecting...</span>
      </div>
    </div>
  </div>
</template>
