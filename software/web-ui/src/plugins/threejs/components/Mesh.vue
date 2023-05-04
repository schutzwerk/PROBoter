<!-- eslint-disable vue/multi-word-component-names -->
<script setup lang="ts">
import {
  onBeforeUnmount,
  onMounted,
  inject,
  provide,
  toRaw,
  type PropType,
} from "vue";
import {
  Mesh,
  PlaneGeometry,
  MeshBasicMaterial,
  DoubleSide,
  Object3D,
  Vector3,
} from "three";
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

const mesh = new Mesh(
  new PlaneGeometry(300, 200),
  new MeshBasicMaterial({ color: 0xffff00, side: DoubleSide })
);

const parentObj = inject<Object3D>("parentObj");
provide("mesh", mesh);

const { setObj, unsetObj } = useObject3D(props);

onMounted(() => {
  setObj(mesh, toRaw(parentObj));
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
