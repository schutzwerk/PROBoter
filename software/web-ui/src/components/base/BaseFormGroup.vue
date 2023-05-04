<script setup lang="ts">
const props = defineProps({
  label: { type: String, default: null },
  description: { type: String, default: null },
  for: { type: String, default: null },
  labelCols: { type: String, default: "12" },
});
</script>

<template>
  <div class="form-input-group row mb-2">
    <div class="col mb-2">
      <div class="row">
        <div :class="['col-' + props.labelCols]">
          <label v-if="props.label" :for="props.for" class="form-label">
            {{ props.label }}
          </label>
        </div>
        <div class="col">
          <slot></slot>
        </div>
      </div>
      <div v-if="description" class="form-text">{{ description }}</div>
    </div>
  </div>
</template>
