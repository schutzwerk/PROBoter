<script setup lang="ts">
import {
  watch,
  ref,
  onMounted,
  onBeforeUnmount,
  inject,
  toRaw,
  type PropType,
} from "vue";
import { Mesh, BufferGeometry, ShapeGeometry, Shape } from "three";

const props = defineProps({
  shapes: {
    type: [Array, Object] as PropType<Shape | Shape[]>,
    default: function () {
      return new Shape();
    },
  },
  curveSegments: {
    type: Number,
    default: 12,
  },
});

watch([() => props.shapes, () => props.curveSegments], () => {
  updateShape();
});

const geometry = ref<ShapeGeometry>(
  new ShapeGeometry(props.shapes, props.curveSegments)
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
  geometry.value = new ShapeGeometry(props.shapes, props.curveSegments);
  if (mesh) {
    mesh.geometry = geometry.value;
  }
}
</script>

<template>
  <div></div>
</template>
