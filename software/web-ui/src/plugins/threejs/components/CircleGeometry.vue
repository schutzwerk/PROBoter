<script setup lang="ts">
import { watch, ref, onMounted, onBeforeUnmount, inject, toRaw } from "vue";
import { CircleGeometry, Mesh, BufferGeometry } from "three";

const props = defineProps({
  radius: {
    type: Number,
    default: 1,
  },
  segments: {
    type: Number,
    default: 8,
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
    () => props.radius,
    () => props.segments,
    () => props.thetaStart,
    () => props.thetaLength,
  ],
  () => {
    updateShape();
  }
);

const geometry = ref<CircleGeometry>(
  new CircleGeometry(
    props.radius,
    props.segments,
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
  geometry.value = new CircleGeometry(
    props.radius,
    props.segments,
    props.thetaStart,
    props.thetaLength
  );
  if (mesh) {
    mesh.geometry = toRaw(geometry.value);
  }
}
</script>

<template>
  <div></div>
</template>
