<script setup lang="ts">
import { onMounted } from "vue";
import Navbar from "@/components/common/Navbar.vue";
import ServerWakeupBanner from "@/components/common/ServerWakeupBanner.vue";
import ErrorToast from "@/components/common/ErrorToast.vue";
import { useEvalStore } from "@/stores/evalStore";

const evalStore = useEvalStore();

onMounted(() => {
  evalStore.fetchConfig();
});
</script>

<template>
  <div class="min-h-screen flex flex-col bg-slate-950 text-slate-100">
    <ServerWakeupBanner />
    <Navbar />

    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <router-view />
    </main>

    <footer class="border-t border-slate-900 py-6 text-center text-xs text-slate-500">
      <div class="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div>
          EvalGen • Zero-Cost Cloud-Native AI Evals Studio
        </div>
        <div class="flex items-center space-x-4">
          <span>FastAPI</span>
          <span>•</span>
          <span>Vue 3</span>
          <span>•</span>
          <span>Google Gemini</span>
          <span>•</span>
          <span>MCP</span>
        </div>
      </div>
    </footer>

    <!-- Global Floating Error Toast Notifications -->
    <ErrorToast />
  </div>
</template>
