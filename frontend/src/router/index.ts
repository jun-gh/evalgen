import { createRouter, createWebHistory } from "vue-router";
import DashboardView from "@/views/DashboardView.vue";
import GeneratorView from "@/views/GeneratorView.vue";
import EvalDetailView from "@/views/EvalDetailView.vue";

const routes = [
  {
    path: "/",
    name: "dashboard",
    component: DashboardView,
  },
  {
    path: "/generate",
    name: "generator",
    component: GeneratorView,
  },
  {
    path: "/evals/:id",
    name: "eval-detail",
    component: EvalDetailView,
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});
