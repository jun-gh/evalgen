<script setup lang="ts">
import { useUiStore } from "@/stores/uiStore";
import { AlertCircle, CheckCircle2, AlertTriangle, Info, X, RotateCcw } from "lucide-vue-next";

const uiStore = useUiStore();
</script>

<template>
  <div class="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 max-w-md w-full pointer-events-none px-4 sm:px-0">
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
          'bg-rose-950/90 border-rose-800 text-rose-100': toast.type === 'error',
          'bg-emerald-950/90 border-emerald-800 text-emerald-100': toast.type === 'success',
          'bg-amber-950/90 border-amber-800 text-amber-100': toast.type === 'warning',
          'bg-slate-900/90 border-slate-700 text-slate-100': toast.type === 'info',
        }"
      >
        <div class="flex items-start gap-3">
          <div class="mt-0.5 flex-shrink-0">
            <AlertCircle v-if="toast.type === 'error'" class="w-5 h-5 text-rose-400" />
            <CheckCircle2 v-else-if="toast.type === 'success'" class="w-5 h-5 text-emerald-400" />
            <AlertTriangle v-else-if="toast.type === 'warning'" class="w-5 h-5 text-amber-400" />
            <Info v-else class="w-5 h-5 text-slate-400" />
          </div>

          <div class="flex-1 min-w-0">
            <h4 class="text-sm font-semibold tracking-tight">{{ toast.title }}</h4>
            <p class="text-xs mt-1 text-slate-300 leading-relaxed">{{ toast.message }}</p>

            <div v-if="toast.trace_id" class="mt-2 text-[10px] font-mono text-slate-400 bg-black/30 px-2 py-0.5 rounded inline-block">
              trace: {{ toast.trace_id }}
            </div>

            <div v-if="toast.retryable && toast.onRetry" class="mt-3">
              <button
                @click="toast.onRetry()"
                class="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-lg bg-white/10 hover:bg-white/20 text-white transition"
              >
                <RotateCcw class="w-3.5 h-3.5" />
                Retry Request
              </button>
            </div>
          </div>

          <button
            @click="uiStore.removeToast(toast.id)"
            class="text-slate-400 hover:text-white p-1 rounded transition"
            title="Dismiss notification"
          >
            <X class="w-4 h-4" />
          </button>
        </div>
      </div>
    </transition-group>
  </div>
</template>
