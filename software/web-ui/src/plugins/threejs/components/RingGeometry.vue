<script setup lang="ts">
import { watch, ref, onMounted, onBeforeUnmount, inject, toRaw } from "vue";
import { Mesh, RingGeometry, BufferGeometry } from "three";

const props = defineProps({
  innerRadius: {
    type: Number,
    default: 0.5,
  },
  outerRadius: {
    type: Number,
    default: 1,
  },
  thetaSegments: {
    type: Number,
    default: 8,
  },
  phiSegments: {
    type: Number,
    default: 1,
  },
  thetaStart: {
    type: Number,
    default: 0,
  },
  thetaLength: {
    type: Number,
    default: Math.PI * 2,
  },
});

watch(
  [
    () => props.innerRadius,
    () => props.outerRadius,
    () => props.thetaSegments,
    () => props.phiSegments,
    () => props.thetaStart,
    () => props.thetaLength,
  ],
  () => {
    updateShape();
  }
);

const geometry = ref<RingGeometry>(
  new RingGeometry(
    props.innerRadius,
    props.outerRadius,
    props.thetaSegments,
    props.phiSegments,
    props.thetaStart,
    props.thetaLength
  )
);
const mesh = inject<Mesh | undefined>("mesh", undefined);

onMounted(() => {
  if (mesh) {
    mesh.geometry = toRaw(geometry.value);
  }
});

onBeforeUnmount(() => {
  if (mesh) {
    mesh.geometry = new BufferGeometry();
  }
  geometry.value.dispose();
});

function updateShape() {
  geometry.value.dispose();
  geometry.value = new RingGeometry(
    props.innerRadius,
    props.outerRadius,
    props.thetaSegments,
    props.phiSegments,
    props.thetaStart,
    props.thetaLength
  );
  if (mesh) {
    mesh.geometry = geometry.value;
  }
}
</script>

<template>
  <div></div>
</template>
