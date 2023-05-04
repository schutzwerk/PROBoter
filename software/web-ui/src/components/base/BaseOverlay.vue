<script setup lang="ts">
const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
});
</script>

<template>
  <div class="overlay-container">
    <slot></slot>

    <div v-if="props.show" class="overlay">
      <slot name="overlay"></slot>
    </div>
  </div>
</template>

<style scoped lang="scss">
.overlay-container {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  vertical-align: stretch;
  height: 100%;
}

.overlay {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  right: 0;
  border-radius: inherit;
  background-color: rgba($color: #262626, $alpha: 0.6);
  display: flex;
  flex-direction: column;
  align-items: stretch;
  z-index: 100;
}
</style>
