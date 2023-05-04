<!-- eslint-disable vue/multi-word-component-names -->
<script setup lang="ts">
import { onMounted, onBeforeUnmount, provide, ref, reactive, toRaw } from "vue";
import log from "js-vue-logger";
import TWEEN from "@tweenjs/tween.js";
import { Camera, PerspectiveCamera, Scene, WebGLRenderer } from "three";

const renderer = new WebGLRenderer({ antialias: true });

const container = ref();

interface RootState {
  scene?: Scene;
  camera?: Camera;
}
const state = reactive({
  scene: undefined,
  camera: undefined,
} as RootState);

onMounted(() => {
  log.info("[Renderer] onMounted");
  renderer.setClearColor(0x808080);
  renderer.setSize(100, 200);

  container.value.appendChild(renderer.domElement);

  onResize();
  animate();
  window.addEventListener("resize", onResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", onResize);
});

function animate() {
  requestAnimationFrame(animate);
  // Update all running tweens
  TWEEN.update();
  // Render the scence
  if (state.camera && state.scene) {
    renderer.render(toRaw(state.scene), toRaw(state.camera));
  }
}

function onResize() {
  if (!container.value) return;

  let containerSize = container.value?.getBoundingClientRect();
  renderer.setSize(containerSize.width, containerSize.height);
  if (state.camera && state.camera.name === "PerspectiveCamera") {
    let perspectiveCamera = state.camera as PerspectiveCamera;
    perspectiveCamera.aspect = containerSize.width / containerSize.height;
  }
}

function registerScene(scene: Scene) {
  log.info("[Renderer] registerScence", scene);
  state.scene = scene;
}
1;

function registerCamera(camera: Camera) {
  log.info("[Renderer] registerCamera", camera);
  state.camera = camera;
}

provide("renderer", renderer);
provide("registerScene", registerScene);
provide("registerCamera", registerCamera);

defineExpose({
  threeRenderer: renderer,
});
</script>

<template>
  <div class="threejs-renderer">
    <slot></slot>
    <div ref="container" class="threejs-container" />
  </div>
</template>

<style scoped>
.threejs-renderer {
  height: 100%;
}
.threejs-renderer .threejs-container {
  width: 100%;
  height: 100%;
}
</style>
