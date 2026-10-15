<script setup lang="ts">
import { useUiStore } from "@/stores/uiStore";
import { Server, RefreshCw } from "lucide-vue-next";

const uiStore = useUiStore();
</script>

<template>
  <div
    v-if="uiStore.isServerWakingUp"
    class="bg-amber-500/10 border-b border-amber-500/30 text-amber-200 px-4 py-2.5 text-xs sm:text-sm flex items-center justify-between transition"
  >
    <div class="max-w-7xl mx-auto flex items-center gap-2.5 w-full">
      <div class="p-1 rounded bg-amber-500/20 text-amber-400 animate-pulse">
        <Server class="w-4 h-4" />
      </div>
      <div class="flex-1">
        <span class="font-semibold text-amber-300">Waking up backend service:</span>
        <span class="ml-1 text-amber-200/90">
          Render's zero-cost tier scales to zero when idle. Your first request is waking the server up (~30-45s) and will auto-complete.
        </span>
      </div>
      <div class="flex items-center gap-1.5 text-xs text-amber-400 font-mono">
        <RefreshCw class="w-3.5 h-3.5 animate-spin" />
        <span>Connecting</span>
      </div>
    </div>
  </div>
</template>
