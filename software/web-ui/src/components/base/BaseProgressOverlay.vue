<script setup lang="ts">
import BaseOverlay from "@/components/base/BaseOverlay.vue";

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  progress: {
    type: Number,
    default: 0,
  },
  text: {
    type: String,
    default: "",
  },
  showProgress: {
    type: Boolean,
    default: false,
  },
});
</script>

<template>
  <base-overlay :show="props.show">
    <template #overlay>
      <div class="progress-overlay-container">
        <div class="spinner-border" role="status"></div>
        <div v-if="props.showProgress">
          {{ props.progress.toFixed(1).toString() + "%" }}
        </div>
        <div class="mb-3">{{ props.text }}</div>
        <slot name="progess-ext"></slot>
      </div>
    </template>
    <slot></slot>
  </base-overlay>
</template>

<style scoped>
.progress-overlay-container {
  margin: auto;
  text-align: center;
}
</style>
