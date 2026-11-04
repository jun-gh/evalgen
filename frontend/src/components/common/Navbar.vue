<script setup lang="ts">
import { RouterLink } from "vue-router";
import { Sun, Moon } from "lucide-vue-next";
import { useUiStore } from "@/stores/uiStore";

const uiStore = useUiStore();
</script>

<template>
  <header class="border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur sticky top-0 z-40 transition-colors">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <RouterLink to="/" class="flex items-center space-x-2.5 group">
          <!-- App Logo: First letter of app name in caps (matches Favicon) -->
          <svg class="w-8 h-8 rounded-lg shadow-sm group-hover:scale-105 transition-transform duration-150 select-none shrink-0" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <defs>
              <linearGradient id="evalgen-nav-logo-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#10b981" />
                <stop offset="100%" stop-color="#047857" />
              </linearGradient>
            </defs>
            <rect width="32" height="32" rx="7" fill="url(#evalgen-nav-logo-grad)" />
            <text
              x="16"
              y="16.5"
              font-family="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Inter, sans-serif"
              font-size="21"
              font-weight="800"
              fill="#ffffff"
              text-anchor="middle"
              dominant-baseline="central"
            >E</text>
          </svg>
          <span class="font-bold text-lg tracking-tight text-slate-900 dark:text-white">
            EvalGen
          </span>
        </RouterLink>
      </div>

      <div class="flex items-center space-x-2">
        <!-- Light / Dark Theme Toggle Button -->
        <button
          @click="uiStore.toggleTheme"
          type="button"
          class="p-2 text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors flex items-center justify-center min-w-[36px] min-h-[36px]"
          :title="uiStore.theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'"
          :aria-label="uiStore.theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'"
        >
          <Sun v-if="uiStore.theme === 'dark'" class="w-4 h-4 text-amber-400 hover:text-amber-300 transition" />
          <Moon v-else class="w-4 h-4 text-slate-600 hover:text-slate-900 transition" />
        </button>
      </div>
    </div>
  </header>
</template>
