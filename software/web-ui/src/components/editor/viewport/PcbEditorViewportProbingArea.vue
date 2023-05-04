<script setup lang="ts">
/**
 * Component to visualize the PROBoter probing area
 * as line grid
 */
import { computed } from "vue";
import ThreeMesh from "@/plugins/threejs/components/Mesh.vue";
import Group from "@/plugins/threejs/components/Group.vue";
import MeshBasicMaterial from "@/plugins/threejs/components/MeshBasicMaterial.vue";
import PlaneGeometry from "@/plugins/threejs/components/PlaneGeometry.vue";
import GridHelper from "@/plugins/threejs/components/GridHelper.vue";
import * as THREE from "three";

import { usePcbEditorStore } from "@/stores/pcbEditor";

const props = defineProps({
  sizeX: {
    type: Number,
    default: 300,
  },
  sizeY: {
    type: Number,
    default: 200,
  },
  gridX: {
    type: Number,
    default: 5,
  },
  gridY: {
    type: Number,
    default: 5,
  },
  isGridVisible: {
    type: Boolean,
    default: true,
  },
});

const store = usePcbEditorStore();

const size = computed(() => {
  return [props.sizeX, props.sizeY];
});
const gridDivisions = computed(() => {
  return [
    Math.max(1, Math.round(props.sizeX / props.gridX)),
    Math.max(1, Math.round(props.sizeY / props.gridY)),
  ];
});
const userData = computed(() => {
  return {
    type: "PROBING_AREA",
    object: null,
    isSelectable: false,
  };
});
</script>

<template>
  <group :position="new THREE.Vector3(0, 0, -0.1)">
    <!-- Grid -->
    <grid-helper
      v-if="isGridVisible"
      :size="size"
      :divisions="gridDivisions"
      :render-order="store.renderOrderProbingAreaGrid"
    />

    <!-- Probing plane -->
    <three-mesh :render-order="1" :user-data="userData">
      <plane-geometry :width="props.sizeX" :height="props.sizeY" />
      <mesh-basic-material :color="store.probingAreaColor" />
    </three-mesh>
  </group>
</template>
