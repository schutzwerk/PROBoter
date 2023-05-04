<script setup lang="ts">
/**
 * Component to draw an axes system on a threejs renderer
 */
import type { PropType } from "vue";
import BufferGeometry from "@/plugins/threejs/components/BufferGeometry.vue";
import LineBasicMaterial from "@/plugins/threejs/components/LineBasicMaterial.vue";
import LineThree from "@/plugins/threejs/components/Line.vue";
import Group from "@/plugins/threejs/components/Group.vue";
import { Vector3 } from "three";

const props = defineProps({
  position: {
    type: Object as PropType<Vector3>,
    default: () => new Vector3(),
  },
  rotation: {
    type: Object as PropType<Vector3>,
    default: () => new Vector3(),
  },
  length: {
    type: Number,
    default: 10,
  },
  height: {
    type: Number,
    default: 0.2,
  },
});
</script>

<template>
  <group :position="props.position" :rotation="props.rotation">
    <line-three>
      <buffer-geometry
        :vertices="[
          [0, 0, 0],
          [10, 0, 0],
        ]"
      />
      <line-basic-material
        :color="0xff0000"
        :linewidth="7"
        :opacity="0.75"
        :transparent="true"
      />
    </line-three>
    <line-three>
      <buffer-geometry
        :vertices="[
          [0, 0, 0],
          [0, 10, 0],
        ]"
      />
      <line-basic-material
        :color="0x00ff00"
        :linewidth="9"
        :transparent="true"
        :opacity="0.75"
      />
    </line-three>
    <line-three>
      <buffer-geometry
        :vertices="[
          [0, 0, 0],
          [0, 0, 10],
        ]"
      />
      <line-basic-material
        :color="0x0000ff"
        :linewidth="5"
        :opacity="0.75"
        :transparent="true"
      />
    </line-three>
  </group>
</template>
