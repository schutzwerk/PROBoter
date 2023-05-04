<script setup lang="ts">
import { computed } from "vue";
import proboter from "@/api/proboter";
import { useProboterStore } from "@/stores/proboter";

const props = defineProps({
  cameraIndex: {
    type: Number,
    required: true,
  },
  undistort: {
    type: Boolean,
    default: false,
  },
});

const proboterStore = useProboterStore();

const cameraFeedUrl = computed<string>(() => {
  return proboter.getStaticCameraFeedUrl(props.cameraIndex);
});

const imageWidth = computed(
  () =>
    proboterStore.getStaticCameraByIndex(props.cameraIndex)?.resolution[0] ||
    640
);

const imageHeight = computed(
  () =>
    proboterStore.getStaticCameraByIndex(props.cameraIndex)?.resolution[1] ||
    480
);
</script>

<template>
  <!-- Container for the actual camera view -->
  <div class="align-items-center d-flex justify-content-center">
    <img
      :src="cameraFeedUrl"
      class="video-viewer"
      :width="imageWidth"
      :height="imageHeight"
    />
  </div>
</template>

<style scoped>
.video-viewer {
  display: block;
  max-width: 100%;
  width: auto;
  height: auto;
}
</style>
