<!-- eslint-disable vue/multi-word-component-names -->
<script setup lang="ts">
import {
  onBeforeUnmount,
  onMounted,
  inject,
  provide,
  type PropType,
} from "vue";
import { Line, Object3D, Vector3 } from "three";
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
});

const line = new Line();
const parentObj = inject<Object3D>("parentObj");
provide("mesh", line);

const { setObj, unsetObj } = useObject3D(props);

onMounted(() => {
  setObj(line, parentObj);
});

onBeforeUnmount(() => {
  unsetObj();
});
</script>

<template>
  <div>
    <slot></slot>
  </div>
</template>
