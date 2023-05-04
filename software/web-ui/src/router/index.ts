import { createRouter, createWebHistory } from "vue-router";
import PcbView from "@/views/PcbView.vue";
import HomeView from "@/views/HomeView.vue";
import ProboterControlView from "@/views/ProboterControlView.vue";
import PcbEditView from "@/views/PcbEditView.vue";
import DemoView from "@/views/DemoView.vue";

import { routes as pcbEditorRoutes } from "./editor";
import { routes as proboterRoutes } from "./proboter";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "home",
      component: HomeView,
    },
    {
      path: "/proboter",
      name: "proboter-control",
      component: ProboterControlView,
      children: proboterRoutes,
    },
    {
      path: "/pcbs",
      name: "pcbs",
      children: [
        { path: "index", name: "pcb-index", component: PcbView },
        {
          path: ":pcbId",
          component: PcbEditView,
          props: (route) => ({ pcbId: Number.parseInt(route.params.pcbId[0]) }),
          children: pcbEditorRoutes,
        },
      ],
    },
    {
      path: "/demo-mode",
      name: "demo-mode",
      component: DemoView,
    },
  ],
});

export default router;
