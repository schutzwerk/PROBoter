<script setup lang="ts">
import { onBeforeUnmount, onMounted, watch, inject, provide } from "vue";
import { MeshBasicMaterial, Mesh, Color, DoubleSide } from "three";
import useMaterial from "./useMaterial";

const props = defineProps({
  name: {
    type: String,
    default: undefined,
  },
  opacity: {
    type: Number,
    default: 1.0,
  },
  side: {
    type: Number,
    default: DoubleSide,
  },
  transparent: {
    type: Boolean,
    default: false,
  },
  userData: {
    type: Object,
    default: null,
  },
  visible: {
    type: Boolean,
    default: true,
  },
  color: {
    type: [Color, String, Number],
    default: 0xff0000,
  },
});

watch(
  () => props.color,
  (newColor) => {
    material.color = new Color(newColor);
  }
);

const material = new MeshBasicMaterial({ color: props.color });
provide("material", material);
const mesh = inject<Mesh | undefined>("mesh");
const { setObj, unsetObj } = useMaterial(props);

onMounted(() => {
  setObj(material, mesh);
});

onBeforeUnmount(() => {
  unsetObj();
  material.dispose();
});
</script>

<template>
  <div>
    <slot></slot>
  </div>
</template>
