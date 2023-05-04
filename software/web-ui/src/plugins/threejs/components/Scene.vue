<!-- eslint-disable vue/multi-word-component-names -->
<script setup lang="ts">
/* eslint-disable no-duplicate-imports */
import {
  onMounted,
  provide,
  watch,
  inject,
  onBeforeUnmount,
  type PropType,
} from "vue";
import log from "js-vue-logger";
import { Scene } from "three";
import * as THREE from "three";
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
    type: Object as PropType<THREE.Vector3>,
    default: () => new THREE.Vector3(),
  },
  rotation: {
    type: Object as PropType<THREE.Vector3>,
    default: () => new THREE.Vector3(),
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
  background: {
    type: [String, Number],
    default: "red",
  },
});

watch(
  () => props.background,
  (newBackground) => {
    setBackgroundColor(newBackground);
  }
);

const scene = new Scene();
provide("parentObj", scene);
const { setObj, unsetObj } = useObject3D(props);
const registerScene = inject<(scene: Scene) => void>("registerScene");

onMounted(() => {
  log.info("[Scene] onMounted");
  // for threejs-inspector to work
  // https://github.com/jeromeetienne/threejs-inspector
  if (import.meta.env.DEV) {
    window.THREE = THREE;
    //window.scene = scene;
  }
  setObj(scene);
  setBackgroundColor(props.background);
  if (registerScene) {
    registerScene(scene);
  }
});

onBeforeUnmount(() => {
  log.info("[Scene] onBeforeUnmount");
  unsetObj();
});

function setBackgroundColor(color: string | number | null) {
  log.info("[Scene] setBackgroundColor:", color);
  if (color != null) {
    scene.background = new THREE.Color(color);
  } else {
    scene.background = null;
  }
}
defineExpose({
  threeScene: scene,
});
</script>

<template>
  <div>
    <slot></slot>
  </div>
</template>
