<script setup lang="ts">
/**
 * Component to draw a PCB scan
 */
import { computed } from "vue";
import type { PropType } from "vue";
import ThreeMesh from "@/plugins/threejs/components/Mesh.vue";
import Texture from "@/plugins/threejs/components/Texture.vue";
import MeshBasicMaterial from "@/plugins/threejs/components/MeshBasicMaterial.vue";
import PlaneGeometry from "@/plugins/threejs/components/PlaneGeometry.vue";
import { Vector3 } from "three";
import type { Scan } from "@/models";
import { pcbApi } from "@/api";
import { usePcbEditorStore } from "@/stores/pcbEditor";

const store = usePcbEditorStore();

const props = defineProps({
  scan: {
    type: Object as PropType<Scan>,
    required: true,
  },
});

const imageUrl = computed(() => pcbApi.getScanImageUrl(props.scan));
const scanWidth = computed(() => props.scan.xMax - props.scan.xMin);
const scanHeight = computed(() => props.scan.yMax - props.scan.yMin);
const position = computed(() => {
  return new Vector3(
    (props.scan.xMax + props.scan.xMin) * 0.5,
    (props.scan.yMax + props.scan.yMin) * 0.5,
    0
  );
});
</script>

<template>
  <three-mesh
    v-if="scan.isVisible"
    :position="position"
    :render-order="store.renderOrderPcbScans"
  >
    <plane-geometry :width="scanWidth" :height="scanHeight" />
    <mesh-basic-material>
      <texture :url="imageUrl" />
    </mesh-basic-material>
  </three-mesh>
</template>
