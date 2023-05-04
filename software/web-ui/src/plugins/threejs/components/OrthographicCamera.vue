<script setup lang="ts">
import { inject, onBeforeUnmount, onMounted, type PropType } from "vue";
import log from "js-vue-logger";
import { Camera, OrthographicCamera, Object3D, Vector3 } from "three";
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

const registerCamera = inject<(camera: Camera) => void>("registerCamera");
const frustumSize = 300;
const aspect = window.innerWidth / window.innerHeight;
const camera = new OrthographicCamera(
  (frustumSize * aspect) / -2,
  (frustumSize * aspect) / 2,
  frustumSize / 2,
  frustumSize / -2,
  0.1,
  2000
);
const parentObj = inject<Object3D>("parentObj");
const { setObj, unsetObj } = useObject3D(props);

onMounted(() => {
  log.info("[OrthographicCamera] onMounted");
  setObj(camera, parentObj);
  camera.position.z = 200;
  if (registerCamera) {
    registerCamera(camera);
  }
});

onBeforeUnmount(() => {
  log.info("[OrthographicCamera] onBeforeUnmount");
  unsetObj();
});

defineExpose({
  threeCamera: camera,
  frustumSize: frustumSize,
});
</script>

<template>
  <div>
    <slot></slot>
  </div>
</template>
