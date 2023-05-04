<script setup lang="ts">
import { inject, watch, onMounted, onBeforeUnmount, type PropType } from "vue";
import { type Mesh, BufferGeometry, BufferAttribute } from "three";

const props = defineProps({
  vertices: {
    type: Array as PropType<Array<Array<number>>>,
    default: () => [],
  },
});

watch(
  () => props.vertices,
  (newVertices) => {
    updateVertices(newVertices);
  }
);

const geometry = new BufferGeometry();
const mesh = inject<Mesh | undefined>("mesh", undefined);

function updateVertices(vertices: Array<Array<number>>) {
  let vLen = 3;
  let vFlattened: Array<number> = [];
  if (vertices.length > 1) {
    vLen = vertices[0].length;
    vertices.forEach((e) => {
      e.forEach((ee) => {
        vFlattened.push(ee);
      });
    });
  }
  geometry.setAttribute(
    "position",
    new BufferAttribute(new Float32Array(vFlattened), vLen)
  );
}

onMounted(() => {
  updateVertices(props.vertices);
  if (mesh) {
    mesh.geometry = geometry;
  }
});

onBeforeUnmount(() => {
  if (mesh) {
    mesh.geometry = new BufferGeometry();
  }
  geometry.dispose();
});
</script>

<template>
  <div></div>
</template>
