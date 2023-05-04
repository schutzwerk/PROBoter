<script setup lang="ts">
import { onBeforeUnmount, onMounted, watch, inject } from "vue";
import { LineBasicMaterial, Line, Color, DoubleSide } from "three";
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
    default: 0x000000,
  },
  linewidth: {
    type: Number,
    default: 2,
  },
});

watch(
  () => props.color,
  (newColor) => {
    material.color = new Color(newColor);
  }
);
watch(
  () => props.linewidth,
  (newLinewidth) => {
    material.linewidth = newLinewidth;
  }
);

const material = new LineBasicMaterial({ color: props.color });
const mesh = inject<Line | undefined>("mesh", undefined);
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
  <div></div>
</template>
