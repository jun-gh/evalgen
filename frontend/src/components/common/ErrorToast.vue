<script setup lang="ts">
import { useUiStore } from "@/stores/uiStore";
import { AlertCircle, CheckCircle2, AlertTriangle, Info, X, RotateCcw } from "lucide-vue-next";

const uiStore = useUiStore();
</script>

<template>
  <div class="fixed bottom-4 left-4 right-4 sm:left-auto sm:right-5 sm:bottom-5 z-50 flex flex-col gap-2.5 max-w-md pointer-events-none">
    <transition-group
      enter-active-class="transform ease-out duration-300 transition"
      enter-from-class="translate-y-2 opacity-0 sm:translate-y-0 sm:translate-x-2"
      enter-to-class="translate-y-0 opacity-100 sm:translate-x-0"
      leave-active-class="transition ease-in duration-200"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-for="toast in uiStore.toasts"
        :key="toast.id"
        class="pointer-events-auto rounded-xl border p-4 shadow-xl backdrop-blur-md transition"
        :class="{
          'bg-rose-50 border-rose-200 text-rose-950 dark:bg-rose-950/90 dark:border-rose-800 dark:text-rose-100': toast.type === 'error',
          'bg-emerald-50 border-emerald-200 text-emerald-950 dark:bg-emerald-950/90 dark:border-emerald-800 dark:text-emerald-100': toast.type === 'success',
          'bg-amber-50 border-amber-200 text-amber-950 dark:bg-amber-950/90 dark:border-amber-800 dark:text-amber-100': toast.type === 'warning',
          'bg-white border-slate-200 text-slate-900 dark:bg-slate-900/90 dark:border-slate-700 dark:text-slate-100': toast.type === 'info',
        }"
      >
        <div class="flex items-start gap-3">
          <div class="mt-0.5 flex-shrink-0">
            <AlertCircle v-if="toast.type === 'error'" class="w-5 h-5 text-rose-600 dark:text-rose-400" />
            <CheckCircle2 v-else-if="toast.type === 'success'" class="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            <AlertTriangle v-else-if="toast.type === 'warning'" class="w-5 h-5 text-amber-600 dark:text-amber-400" />
            <Info v-else class="w-5 h-5 text-slate-500 dark:text-slate-400" />
          </div>

          <div class="flex-1 min-w-0">
            <h4 class="text-sm font-semibold tracking-tight">{{ toast.title }}</h4>
            <p class="text-xs mt-1 text-slate-700 dark:text-slate-300 leading-relaxed">{{ toast.message }}</p>

            <div class="flex flex-wrap items-center gap-1.5 mt-2">
              <span v-if="toast.retry_count" class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-rose-200/80 dark:bg-rose-900/60 text-rose-800 dark:text-rose-200">
                {{ toast.retry_count }} retries exhausted
              </span>
              <span v-if="toast.trace_id" class="text-[10px] font-mono text-slate-600 bg-slate-200/60 dark:text-slate-400 dark:bg-black/30 px-2 py-0.5 rounded">
                trace: {{ toast.trace_id }}
              </span>
            </div>

            <div v-if="toast.retryable && toast.onRetry" class="mt-3">
              <button
                @click="toast.onRetry()"
                class="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-lg bg-slate-200/80 hover:bg-slate-300 dark:bg-white/10 dark:hover:bg-white/20 text-slate-900 dark:text-white transition"
              >
                <RotateCcw class="w-3.5 h-3.5" />
                Retry Request
              </button>
            </div>
          </div>

          <button
            @click="uiStore.removeToast(toast.id)"
            class="text-slate-400 hover:text-slate-700 dark:hover:text-white p-1 rounded transition"
            title="Dismiss notification"
          >
            <X class="w-4 h-4" />
          </button>
        </div>
      </div>
    </transition-group>
  </div>
</template>
