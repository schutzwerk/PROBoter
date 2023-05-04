<!-- eslint-disable vue/multi-word-component-names -->
<script setup lang="ts">
import { watch, onMounted, onBeforeUnmount, inject, ref } from "vue";
import log from "js-vue-logger";
import { TextureLoader, MeshBasicMaterial, Texture, Color } from "three";

const props = defineProps({
  url: { type: String, default: null },
});

watch(
  () => props.url,
  () => {
    updateTexture();
  }
);

const material = inject<MeshBasicMaterial | undefined>("material", undefined);
const texture = ref<Texture | undefined>(undefined);

onMounted(() => {
  updateTexture();
});

onBeforeUnmount(() => {
  if (material) {
    material.map = null;
  }
  texture.value?.dispose();
});

function updateTexture() {
  log.info("[Texture] Update");
  texture.value?.dispose();
  texture.value = new TextureLoader().load(props.url);
  if (material) {
    material.map = texture.value;
    // Rest of color is required for correct visualization of the texture image!
    material.color = new Color(0xffffff);
  }
}
</script>

<template>
  <div></div>
</template>
