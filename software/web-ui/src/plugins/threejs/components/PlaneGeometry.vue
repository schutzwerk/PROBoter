<script setup lang="ts">
import { watch, ref, onMounted, onBeforeUnmount, inject, toRaw } from "vue";
import { PlaneGeometry, Mesh, BufferGeometry } from "three";

const props = defineProps({
  width: {
    type: Number,
    default: 1,
  },
  height: {
    type: Number,
    default: 1,
  },
  widthSegments: {
    type: Number,
    default: 1,
  },
  heightSegments: {
    type: Number,
    default: 1,
  },
});

watch(
  [
    () => props.width,
    () => props.height,
    () => props.widthSegments,
    () => props.heightSegments,
  ],
  () => {
    updateShape();
  }
);

const geometry = ref<PlaneGeometry>(
  new PlaneGeometry(
    props.width,
    props.height,
    props.widthSegments,
    props.heightSegments
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
  geometry.value = new PlaneGeometry(
    props.width,
    props.height,
    props.widthSegments,
    props.heightSegments
  );
  if (mesh) {
    mesh.geometry = toRaw(geometry.value);
  }
}
</script>

<template>
  <div></div>
</template>
