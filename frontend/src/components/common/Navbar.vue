<script setup lang="ts">
import { RouterLink } from "vue-router";
import { Sparkles, Layers, Cpu } from "lucide-vue-next";
</script>

<template>
  <header class="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-40">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <RouterLink to="/" class="flex items-center space-x-2.5 group">
          <div class="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 group-hover:border-emerald-500/50 transition">
            <Sparkles class="w-5 h-5" />
          </div>
          <div>
            <span class="font-bold text-lg tracking-tight text-white flex items-center gap-1.5">
              EvalGen
              <span class="text-xs px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                v0.1
              </span>
            </span>
          </div>
        </RouterLink>
      </div>

      <nav class="flex items-center space-x-1 sm:space-x-3">
        <RouterLink
          to="/"
          class="px-3 py-1.5 rounded-lg text-sm font-medium transition"
          :class="$route.path === '/' ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'"
        >
          <span class="flex items-center gap-1.5">
            <Layers class="w-4 h-4" />
            Eval Sets
          </span>
        </RouterLink>

        <RouterLink
          to="/generate"
          class="px-3.5 py-1.5 rounded-lg text-sm font-medium bg-emerald-600 hover:bg-emerald-500 text-white shadow-sm transition flex items-center gap-1.5"
        >
          <Sparkles class="w-4 h-4" />
          New Generation
        </RouterLink>

        <a
          href="/api/v1/health"
          target="_blank"
          class="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition"
          title="Backend Health & Cold-Start Status"
        >
          <Cpu class="w-4 h-4" />
        </a>
      </nav>
    </div>
  </header>
</template>
