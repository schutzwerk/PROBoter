<script setup lang="ts">
/**
 * Component to control a single camera (movable or static)
 */

import { computed } from "vue";
import type { PropType } from "vue";
import { BIconGear, BIconCalculator } from "bootstrap-icons-vue";
import ProboterCameraFeedView from "./ProboterCameraFeedView.vue";
import ProboterEntityContainer from "@/components/proboter/ProboterEntityContainer.vue";
import type { EntityStatus } from "@/components/proboter/ProboterEntityContainer.vue";
import type { Camera } from "@/models";

const props = defineProps({
  /**
   * The camera instance to control
   */
  camera: {
    type: Object as PropType<Camera>,
    default: null,
  },
  isMovable: {
    type: Boolean,
  },
});

const cameraStatus = computed<EntityStatus>(() => {
  return {
    title: props.camera.connected ? "CONNECTED" : "DISCONNECTED",
    variant: props.camera.connected ? "okay" : "error",
  };
});
</script>

<template>
  <proboter-entity-container
    :title="'Camera - ' + camera.name"
    :status="cameraStatus"
  >
    <template #controls>
      <!-- Camera settings -->
      <router-link
        class="btn btn-secondary me-2"
        title="Settings"
        :to="{
          name: 'camera-static-settings',
          params: { cameraIndex: props.camera.index },
        }"
      >
        <b-icon-gear aria-hidden="true" />
      </router-link>

      <!-- Camera calibration -->
      <router-link
        class="btn btn-secondary me-2"
        title="Calibration"
        :to="{
          name: 'camera-static-calibration',
          params: { cameraIndex: props.camera.index },
        }"
      >
        <b-icon-calculator aria-hidden="true" />
      </router-link>

      <!-- Camera intrinsic parameter calibration -->
      <router-link
        class="btn btn-secondary me-2"
        title="Intrinsic camera parameter calibration"
        :to="{
          name: 'camera-static-calibration-intrinsics',
          params: { cameraIndex: props.camera.index },
        }"
      >
        <b-icon-calculator aria-hidden="true" />
      </router-link>
    </template>

    <!-- Container for the actual camera view -->
    <proboter-camera-feed-view
      :camera-index="camera.index"
      class="align-middle"
    />
  </proboter-entity-container>
</template>

<style scoped>
.camera-control {
  height: 100%;
}
</style>
