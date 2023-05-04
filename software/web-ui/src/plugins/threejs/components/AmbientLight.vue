<script setup lang="ts">
import {
  onBeforeUnmount,
  onMounted,
  watch,
  inject,
  toRaw,
  type PropType,
} from "vue";
import log from "js-vue-logger";
import { AmbientLight, Color, Object3D, Vector3 } from "three";
import useObject3D from "./useObject3D";

const props = defineProps({
  name: {
    type: String,
    default: "",
  },
  scale: {
    type: Number,
    default: 1.0,
  },
  position: {
    type: Object as PropType<Vector3>,
    default: () => new Vector3(),
  },
  rotation: {
    type: Object as PropType<Vector3>,
    default: () => new Vector3(),
  },
  renderOrder: {
    type: Number,
    default: 0,
  },
  userData: {
    type: Object,
    default: () => ({}),
  },
  visible: {
    type: Boolean,
    default: true,
  },
  color: {
    type: Number,
    default: null,
  },
  intensity: {
    type: Number,
    default: 1.0,
  },
});

watch(
  () => props.color,
  (newColor) => {
    light.color = new Color(newColor);
  }
);

watch(
  () => props.intensity,
  (newIntensity) => {
    light.intensity = newIntensity;
  }
);

const light = new AmbientLight(props.color, props.intensity);
const parentObj = inject<Object3D>("parentObj");
const { setObj, unsetObj } = useObject3D(props);

onMounted(() => {
  log.info("[AmbientLight] onMounted", light);
  setObj(light, toRaw(parentObj));
});

onBeforeUnmount(() => {
  log.info("[AmbientLight] onBeforeUnmount");
  unsetObj();
  light.dispose();
});
</script>

<template>
  <div></div>
</template>
