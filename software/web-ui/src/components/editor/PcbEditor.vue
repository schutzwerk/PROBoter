<script setup lang="ts">
/*
 * Interactive 3D PCB editor
 */
import { onMounted } from "vue";
import { RouterView } from "vue-router";
import log from "js-vue-logger";

import PcbEditorToolbar from "@/components/editor/PcbEditorToolbar.vue";
import PcbEditorStatusBar from "@/components/editor/PcbEditorStatusBar.vue";
import PcbEditorActionButton from "@/components/editor/PcbEditorActionButton.vue";
import PcbEditorProbingPosition from "@/components/editor/PcbEditorProbingPosition.vue";
import PcbEditorViewport from "@/components/editor/viewport/PcbEditorViewport.vue";
import { usePcbEditorStore } from "@/stores/pcbEditor";
import { usePcbStore } from "@/stores/pcbs";

const props = defineProps({
  pcbId: {
    type: Number,
    default: null,
  },
});

const store = usePcbEditorStore();
const pcbStore = usePcbStore();

onMounted(() => {
  log.info("[PcbEditor] onMounted", props.pcbId);
  // Set the currently edited PCB
  store.currentPcbId = props.pcbId;
  pcbStore.fetchPcbById(props.pcbId).then((pcb) => {
    if (pcb) {
      store.probingPlaneZ = -0.5 * pcb.thickness;
    } else {
      store.probingPlaneZ = 0;
    }
  });
});
</script>

<template>
  <!-- Content -->
  <div class="content-wrapper">
    <!-- 3D viewport -->
    <pcb-editor-viewport />

    <!-- Sidebar (extra large layouts only)-->
    <div class="sidebar-xxl d-xxl-flex d-none">
      <router-view class="sidebar-main dp-08" />
      <router-view class="sidebar-detail dp-08" name="detail" />
    </div>

    <!-- Sidebar (default layout) -->
    <div class="sidebar d-xxl-none d-block">
      <router-view v-slot="{ Component }" class="sidebar-main dp-08">
        <transition :name="'fade'">
          <component :is="Component" />
        </transition>
      </router-view>

      <router-view
        v-slot="{ Component }"
        class="sidebar-detail dp-08"
        name="detail"
      >
        <transition :name="'fade'">
          <component :is="Component" />
        </transition>
      </router-view>
    </div>

    <!-- Viewport controls -->
    <pcb-editor-toolbar class="viewport-controls" />

    <!-- Current mouse position on the probing area -->
    <pcb-editor-probing-position class="probing-position" />

    <!-- Status bar -->
    <pcb-editor-status-bar id="pcb-editor-status-bar" ref="statusBar" />

    <!-- Action button -->
    <pcb-editor-action-button class="action-button" />
  </div>
</template>

<style scoped lang="scss">
@import "@/assets/style.scss";

.content-wrapper {
  flex: 1;
  overflow: hidden;
  display: flex;
  align-items: stretch;
  position: relative;
}

.viewport-controls {
  position: absolute;
  top: calc(100% - 50px);
  left: 50%;
  transform: translateX(-50%);
}

.probing-position {
  position: absolute;
  top: 10px;
  right: 10px;
}

#pcb-editor-status-bar {
  position: absolute;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
}

.sidebar,
.sidebar-xxl {
  position: absolute;
  top: 10px;
  left: 10px;
  bottom: 10px;
  padding: 10px;
  text-align: left;
  overflow: hidden;
}

.sidebar,
.sidebar-xxl,
.sidebar > .sidebar-main,
.sidebar > .sidebar-detail {
  width: 380px;
  max-width: 380px;
}

@media (max-width: map-get($grid-breakpoints, "xxl")) {
  .sidebar,
  .sidebar-xxl,
  .sidebar > .sidebar-main,
  .sidebar > .sidebar-detail {
    width: 320px;
    max-width: 320px;
  }
}

.sidebar-xxl {
  flex-flow: column;
  align-items: stretch;
}

.sidebar-xxl > .sidebar-main {
  text-align: left;
  border-radius: 0.25rem;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar > .sidebar-main,
.sidebar > .sidebar-detail {
  position: absolute;
  top: 0;
  left: 0;
  max-height: 100%;
}

.sidebar-xxl > .sidebar-detail {
  margin-top: 10px;
  padding: 10px;
  text-align: left;
  border-radius: 0.25rem;
  overflow-x: hidden;
}

.sidebar-main,
.sidebar-detail {
  border-radius: 0.25rem;
  padding: 20px;
}

.sidebar-main > * {
  height: 100%;
}

.sidebar-detail:empty {
  display: none;
}

.action-button {
  position: absolute;
  bottom: 100px;
  right: 100px;
  font-size: 2em;
}

.fade-enter-active,
.fade-leave-active {
  transition: all 0.5s ease;
  animation-direction: reverse;
}

.fade-enter-from,
.fade-leave-to {
  transform: translate(-380px, 0);
  opacity: 0;
}
</style>
