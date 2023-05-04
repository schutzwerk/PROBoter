<script setup lang="ts">
const props = defineProps({
  for: { type: String, default: null },
  label: { type: String, default: "" },
  modelValue: {
    type: Boolean,
    required: true,
  },
});

defineEmits(["update:modelValue"]);
</script>

<template>
  <div class="form-check">
    <label class="form-check-label" for="{{ props.for }}">{{
      props.label
    }}</label>
    <input
      id="{{ props.for }}"
      class="form-check-input"
      type="checkbox"
      :value="modelValue"
      required
      @change="
        $emit('update:modelValue', ($event.target as HTMLInputElement).checked)
      "
    />
  </div>
</template>
